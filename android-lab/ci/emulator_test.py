"""Actual Android emulator checks, NOT physical ARM hardware or TapPlay.
UI actions use adb; an explicitly enabled app-private probe supplies observations.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import struct
import subprocess
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'android-lab/build/emulator'
OUT.mkdir(parents=True, exist_ok=True)
SDK = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
ADB = str(SDK / 'platform-tools/adb')
PKG = 'io.github.u1337816143.farmlab.emulator'
SERIAL = 'emulator-5554'
REPORT = {'kind': 'Android emulator, x86_64, API 35; NOT physical ARM hardware or TapPlay', 'commit': os.environ.get('GITHUB_SHA'), 'checks': [], 'result': 'RUNNING'}


def run(args, *, timeout=60, check=True, binary=False):
    p = subprocess.run([str(a) for a in args], capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f'Command failed {args}: {p.stdout.decode(errors="replace")} {p.stderr.decode(errors="replace")}')
    return p.stdout if binary else p.stdout.decode(errors='replace').strip()


def adb(*args, **kwargs):
    return run([ADB, '-s', SERIAL, *args], **kwargs)


def shell(*args, **kwargs):
    return adb('shell', shlex.join([str(a) for a in args]), **kwargs)


def private(*args, **kwargs):
    return shell('run-as', PKG, *args, **kwargs)


def record(label, condition, details=None):
    REPORT['checks'].append({'name': label, 'passed': bool(condition), 'details': details})
    print(f'EMULATOR_CHECK {label}: {bool(condition)}', flush=True)
    if not condition:
        raise AssertionError(label)


def same_snapshot(a, b):
    # Observational probe JSON is rounded. Native checkpoint tests compare exactly.
    return (a.keys() == b.keys() and all(a[k] == b[k] for k in a if k != 'player')
            and len(a['player']) == len(b['player']) == 2
            and all(math.isclose(x, y, rel_tol=0, abs_tol=1e-6) for x, y in zip(a['player'], b['player'])))


def probe(timeout=30, predicate=lambda p: True):
    end = time.monotonic() + timeout
    last = None
    while time.monotonic() < end:
        try:
            last = json.loads(private('cat', 'files/lab_diagnostics.json'))
            if predicate(last):
                (OUT / 'last-probe.json').write_text(json.dumps(last, indent=2))
                return last
        except (ValueError, RuntimeError):
            pass
        time.sleep(0.4)
    raise TimeoutError(f'Runtime probe not ready or expected state not reached: {last}')


def screenshot(name):
    image = adb('exec-out', 'screencap', '-p', binary=True)
    if not image.startswith(b'\x89PNG'):
        raise RuntimeError('Android did not return a PNG screenshot')
    (OUT / name).write_bytes(image)
    return struct.unpack('>II', image[16:24])


def tap(point, p):
    size = screenshot('latest.png')
    x = round(point[0] * size[0] / p['viewport'][0])
    y = round(point[1] * size[1] / p['viewport'][1])
    shell('input', 'tap', x, y)
    time.sleep(0.6)


def launch(old_session=None):
    # Explicit activity start avoids injecting Monkey's random event.
    result = shell('am', 'start', '-W', '-n', PKG + '/com.godot.game.GodotApp')
    with (OUT / 'launches.log').open('a') as f:
        f.write(result + '\n')
    return probe(predicate=lambda p: p['active'] and (old_session is None or p['session'] != old_session))


def main():
    user_home = Path(os.environ['RUNNER_TEMP']) / 'camera-lab-android-home'
    avd_home = user_home / 'avd'
    avd_home.mkdir(parents=True, exist_ok=True)
    os.environ.update(ANDROID_USER_HOME=str(user_home), ANDROID_EMULATOR_HOME=str(user_home), ANDROID_AVD_HOME=str(avd_home))
    sdkmanager = sorted(SDK.glob('cmdline-tools/*/bin/sdkmanager'))[-1]
    avdmanager = sdkmanager.with_name('avdmanager')
    image = 'system-images;android-35;default;x86_64'
    install_log = run([sdkmanager, '--sdk_root=' + str(SDK), 'emulator', image], timeout=360)
    (OUT / 'sdk-install.log').write_text(install_log)
    avd_path = avd_home / 'camera_lab_ci.avd'
    p = subprocess.run([str(avdmanager), 'create', 'avd', '--force', '-n', 'camera_lab_ci', '-k', image, '-p', str(avd_path)], input=b'no\n', capture_output=True, timeout=60)
    (OUT / 'avd-create.log').write_bytes(p.stdout + p.stderr)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    config = avd_path / 'config.ini'
    if not config.is_file():
        raise FileNotFoundError(f'AVD manager did not create its requested config: {config}')
    overrides = {'hw.lcd.width': '1280', 'hw.lcd.height': '720', 'hw.lcd.density': '160', 'hw.keyboard': 'yes', 'hw.ramSize': '2048'}
    text = '\n'.join(line for line in config.read_text().splitlines() if line.partition('=')[0].strip() not in overrides)
    config.write_text(text + '\n' + '\n'.join(f'{k}={v}' for k, v in overrides.items()) + '\n')
    (OUT / 'avd-config.txt').write_text(config.read_text())
    (OUT / 'avd-list.txt').write_text(run([SDK / 'emulator/emulator', '-list-avds']))
    emulator_log = (OUT / 'emulator.log').open('wb')
    process = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', 'camera_lab_ci', '-port', '5554', '-no-window', '-no-audio', '-no-boot-anim', '-no-snapshot', '-no-metrics', '-gpu', 'swiftshader_indirect', '-camera-back', 'none', '-camera-front', 'none', '-cores', '2', '-memory', '2048'], stdout=emulator_log, stderr=subprocess.STDOUT)
    try:
        end = time.monotonic() + 300
        while time.monotonic() < end:
            if process.poll() is not None:
                raise RuntimeError('Emulator exited before boot; inspect emulator.log')
            if shell('getprop', 'sys.boot_completed', check=False) == '1':
                break
            time.sleep(2)
        else:
            raise TimeoutError('Android boot timed out')
        for namespace, key, value in [('global', 'window_animation_scale', '0'), ('global', 'transition_animation_scale', '0'), ('global', 'animator_duration_scale', '0'), ('system', 'accelerometer_rotation', '0')]:
            shell('settings', 'put', namespace, key, value)
        shell('input', 'keyevent', '82')
        # Cold AOSP boot applies theme overlays after boot_completed; let setup settle.
        time.sleep(25)
        apk = OUT.parent / 'farmlab-emulator.apk'
        REPORT['emulator_apk_sha256'] = hashlib.sha256(apk.read_bytes()).hexdigest()
        REPORT['device_properties'] = {'android': shell('getprop', 'ro.build.version.release'), 'api': shell('getprop', 'ro.build.version.sdk'), 'abi': shell('getprop', 'ro.product.cpu.abi')}
        record('APK installation', 'Success' in adb('install', '-r', apk, timeout=120))
        private('mkdir', '-p', 'files')
        private('touch', 'files/ci_probe.enabled')
        adb('logcat', '-c')
        p = launch()
        record('actual Android launch', p['version'] == '0.2.0', p['viewport'])
        screenshot('01-launch.png')
        angle_before = p['angle']
        width, height = screenshot('latest.png')
        point = p['buttons']['TURN R']
        x, y = round(point[0] * width / p['viewport'][0]), round(point[1] * height / p['viewport'][1])
        shell('input', 'swipe', x, y, x, y, 600)
        p = probe(predicate=lambda p: abs(p['angle'] - angle_before) > 0.1 and p['held'] == 0)
        record('Android held-button rotation and release', True)
        tap(p['buttons']['HOME'], p)
        p = probe()
        tap(p['buttons']['PLACE'], p)
        p = probe()
        tap(p['fixture'], p)
        p = probe(predicate=lambda p: [8, 3] in p['snapshot']['markers'])
        record('Android tap picks expected world tile', True)
        screenshot('02-placement.png')
        tap(p['buttons']['MOVE'], p)
        p = probe()
        tap(p['destination'], p)
        moving = probe(predicate=lambda p: p['route'] > 0)
        time.sleep(1)
        shell('input', 'keyevent', 'KEYCODE_HOME')
        paused = probe(predicate=lambda p: not p['active'])
        record('background cancels route and held input', paused['route'] == 0 and paused['held'] == 0 and paused['fingers'] == 0 and paused['checkpoint_ok'])
        expected = paused['snapshot']
        record('actual player moved before pause', expected['player'] != moving['snapshot']['player'])
        shell('am', 'force-stop', PKG)
        p = launch(paused['session'])
        record('process restart restores checkpoint', same_snapshot(p['snapshot'], expected) and p['recovered_from'] == 'primary', {'before': expected, 'after': p['snapshot']})
        screenshot('03-restart.png')
        backup = json.loads(private('cat', 'files/camera_lab_v1.json.bak'))
        expected_backup = json.loads(backup['payload_json']) if 'payload_json' in backup else backup
        shell('am', 'force-stop', PKG)
        private('sh', '-c', 'printf broken > files/camera_lab_v1.json')
        p = launch(p['session'])
        record('corrupt primary recovers actual on-device backup', same_snapshot(p['snapshot'], expected_backup) and p['recovered_from'] == 'bak', {'backup': expected_backup, 'restored': p['snapshot']})
        screenshot('04-backup-recovery.png')
        shell('wm', 'size', '960x540')
        time.sleep(2)
        p = probe()
        record('resized Android viewport controls remain in bounds', p['active'] and all(0 <= b[0] < p['viewport'][0] and 0 <= b[1] < p['viewport'][1] for b in p['buttons'].values()))
        screenshot('05-resized.png')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(2)
        activities = shell('dumpsys', 'activity', 'activities')
        (OUT / 'activities-after-back.txt').write_text(activities)
        resumed = [line for line in activities.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
        record('Android Back leaves the game activity', bool(resumed) and not any(PKG in line for line in resumed), resumed)
        logs = adb('logcat', '-d', '-v', 'threadtime')
        (OUT / 'logcat.txt').write_text(logs)
        record('no observed script errors, shader link failure or fatal exception', all(s not in logs for s in ['SCRIPT ERROR', 'FATAL EXCEPTION', 'Program linking failed']))
        REPORT['result'] = 'PASS'
    finally:
        try:
            screenshot('final-screen.png')
            (OUT / 'final-logcat.txt').write_text(adb('logcat', '-d', '-v', 'threadtime', check=False))
            (OUT / 'private-files.txt').write_text(private('find', '.', '-maxdepth', '3', '-type', 'f', check=False))
            adb('emu', 'kill', check=False)
        finally:
            process.terminate()
            emulator_log.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        REPORT['result'] = 'FAIL'
        REPORT['error'] = repr(exc)
        REPORT['traceback'] = traceback.format_exc()
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(REPORT, ensure_ascii=False, indent=2))
