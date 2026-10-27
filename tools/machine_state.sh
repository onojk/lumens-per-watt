#!/usr/bin/env bash
# tools/machine_state.sh [CORE]: the machine's state for a timed run (PROTOCOL.md). CORE is the pinned core (default 2,
# as lampcore --phasetime runs under taskset -c 2). Read-only; changes nothing.
core=${1:-2}
c=/sys/devices/system/cpu/cpu$core/cpufreq
echo "time: $(date -Is)"
echo "pinned core: $core"
echo "governor: $(cat $c/scaling_governor 2>/dev/null || echo unknown)"
echo "energy_performance_preference: $(cat $c/energy_performance_preference 2>/dev/null || echo unknown)"
echo "cur MHz: $(( $(cat $c/scaling_cur_freq 2>/dev/null || echo 0) / 1000 )); max MHz: $(( $(cat $c/cpuinfo_max_freq 2>/dev/null || echo 0) / 1000 ))"
echo "load average: $(cut -d' ' -f1-3 /proc/loadavg)"
for p in /sys/class/power_supply/*; do
    [ -f "$p/online" ] && echo "power supply $(basename "$p") online: $(cat "$p/online")"
    [ -f "$p/capacity" ] && echo "power supply $(basename "$p") capacity: $(cat "$p/capacity")% ($(cat "$p/status" 2>/dev/null))"
done
for z in /sys/class/thermal/thermal_zone*; do
    t=$(cat "$z/type" 2>/dev/null)
    case "$t" in x86_pkg_temp|TCPU) echo "temperature $t: $(( $(cat "$z/temp") / 1000 )) C";; esac
done
command -v sensors >/dev/null && sensors 2>/dev/null | grep -E "^(Package id|Core $core)" | sed 's/^/sensors: /'
echo "top 5 processes by current CPU (top, a 1 s sample):"
top -b -n 2 -d 1 -o %CPU -w 200 | awk '/^top -/{n++} n==2 && /^ *[0-9]+ /{print "  " $9 "% " $12; if (++k == 5) exit}'
