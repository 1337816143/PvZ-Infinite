"""Real Android emulator smoke test. Not a physical-device or TapPlay test.
Uses adb UI events and debuggable app-private diagnostic output, never web previews.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import time

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


def probe(timeout=30, predicate=lambda p: True):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            p = json.loads(private('cat', 'files/lab_diagnostics.json'))
            if predicate(p):
                return p
        except (ValueError, RuntimeError):
            pass
        time.sleep(0.4)
    raise TimeoutError('Runtime probe not ready or expected state not reached')


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
    shell('monkey', '-p', PKG, '-c', 'android.intent.category.LAUNCHER', '1')
    return probe(predicate=lambda p: p['active'] and (old_session is None or p['session'] != old_session))


def main():
    sdkmanager = sorted(SDK.glob('cmdline-tools/*/bin/sdkmanager'))[-1]
    avdmanager = sdkmanager.with_name('avdmanager')
    image = 'system-images;android-35;default;x86_64'
    run([sdkmanager, '--sdk_root=' + str(SDK), 'emulator', image], timeout=360)
    p = subprocess.run([str(avdmanager), 'create', 'avd', '--force', '-n', 'camera_lab_ci', '-k', image], input=b'no\n', capture_output=True, timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    config = Path.home() / '.android/avd/camera_lab_ci.avd/config.ini'
    with config.open('a') as f:
        f.write('\nhw.lcd.width=1280\nhw.lcd.height=720\nhw.lcd.density=160\nhw.keyboard=yes\nhw.ramSize=2048\n')
    emulator_log = (OUT / 'emulator.log').open('wb')
    process = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', 'camera_lab_ci', '-port', '5554', '-no-window', '-no-audio', '-no-boot-anim', '-no-snapshot', '-gpu', 'swiftshader_indirect', '-camera-back', 'none', '-camera-front', 'none', '-cores', '2', '-memory', '2048'], stdout=emulator_log, stderr=subprocess.STDOUT)
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
        record('process restart restores checkpoint', p['snapshot'] == expected and p['recovered_from'] == 'primary')
        screenshot('03-restart.png')
        backup = json.loads(private('cat', 'files/camera_lab_v1.json.bak'))
        expected_backup = json.loads(backup['payload_json']) if 'payload_json' in backup else backup
        shell('am', 'force-stop', PKG)
        private('sh', '-c', 'printf broken > files/camera_lab_v1.json')
        p = launch(p['session'])
        record('corrupt primary recovers actual on-device backup', p['snapshot'] == expected_backup and p['recovered_from'] == 'bak')
        screenshot('04-backup-recovery.png')
        shell('wm', 'size', '960x540')
        time.sleep(2)
        p = probe()
        record('resized Android viewport remains interactive', p['active'] and all(0 <= b[0] < p['viewport'][0] and 0 <= b[1] < p['viewport'][1] for b in p['buttons'].values()))
        screenshot('05-resized.png')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(1)
        record('Android Back finishes activity', not shell('pidof', PKG, check=False))
        logs = adb('logcat', '-d', '-v', 'threadtime')
        (OUT / 'logcat.txt').write_text(logs)
        record('no observed Godot script errors or app fatal exception', 'SCRIPT ERROR' not in logs and 'FATAL EXCEPTION' not in logs)
        REPORT['result'] = 'PASS'
    finally:
        try:
            (OUT / 'final-logcat.txt').write_text(adb('logcat', '-d', '-v', 'threadtime', check=False))
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
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(REPORT, ensure_ascii=False, indent=2))
