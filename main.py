#!/usr/bin/env python
from __future__ import print_function
import sys
import argparse
from bcc import BPF, PerfType, PerfHWConfig
import signal
from time import sleep
import os

parser = argparse.ArgumentParser(
    description="Summarize cache references and misses by PID",
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument(
    "-c", "--sample_period", type=int, default=100,
    help="Sample one in this many number of cache reference / miss events")
parser.add_argument(
    "duration", nargs="?", default=9, help="Duration, in seconds, to run")
parser.add_argument(
    "-t", "--tid", action="store_true",
    help="Summarize cache references and misses by PID/TID"
)
parser.add_argument("--ebpf", action="store_true",
    help=argparse.SUPPRESS)
args = parser.parse_args()

# load BPF program
bpf_text="""
#include <linux/ptrace.h>
#include <uapi/linux/bpf_perf_event.h>

struct key_t {
    int cpu;
    u32 pid;
    u32 tid;
    char name[TASK_COMM_LEN];
};

BPF_HASH(ref_count, struct key_t);
BPF_HASH(miss_count, struct key_t);

static inline __attribute__((always_inline)) void get_key(struct key_t* key) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    key->cpu = bpf_get_smp_processor_id();
    key->pid = pid_tgid >> 32;
    key->tid = GET_TID ? (u32)pid_tgid : key->pid;
    bpf_get_current_comm(&(key->name), sizeof(key->name));
}

int on_cache_miss(struct bpf_perf_event_data *ctx) {
    struct key_t key = {};
    get_key(&key);

    miss_count.increment(key, ctx->sample_period);

    return 0;
}

int on_cache_ref(struct bpf_perf_event_data *ctx) {
    struct key_t key = {};
    get_key(&key);

    ref_count.increment(key, ctx->sample_period);

    return 0;
}
"""

bpf_text = bpf_text.replace("GET_TID", "1" if args.tid else "0")

if args.ebpf:
    print(bpf_text)
    exit()

b = BPF(text=bpf_text)
try:
    b.attach_perf_event(
        ev_type=PerfType.HARDWARE, ev_config=PerfHWConfig.CACHE_MISSES,
        fn_name="on_cache_miss", sample_period=args.sample_period)
    b.attach_perf_event(
        ev_type=PerfType.HARDWARE, ev_config=PerfHWConfig.CACHE_REFERENCES,
        fn_name="on_cache_ref", sample_period=args.sample_period)
except Exception:
    print("Failed to attach to a hardware event. Is this a virtual machine?")
    exit()

print("Running for {} seconds or hit Ctrl-C to end.".format(args.duration))

try:
    sleep(float(args.duration))
except KeyboardInterrupt:
    signal.signal(signal.SIGINT, lambda signal, frame: print())

miss_count = {}
for (k, v) in b.get_table('miss_count').items():
    if args.tid:
        miss_count[(k.pid, k.tid, k.cpu, k.name)] = v.value
    else:
        miss_count[(k.pid, k.cpu, k.name)] = v.value

tot_ref = 0
tot_miss = 0
if os.path.exists("cpus.txt"):
    os.remove("cpus.txt")
for (k, v) in b.get_table('ref_count').items():
     #if k.cpu == int(sys.argv[1]):
     if k.cpu == 3:
        l = str(k.cpu)
        p = str(k.pid)
        x = str(k.name.decode('utf-8', 'replace'))
        f = open("one.txt", "a")
        f.write("PID: ")
        f.write(p)
        f.write("  \t")
        f.write("NAME: ")
        f.write(x)
        f.write("\n")
        f.close()
     l = str(k.cpu)
     p = str(k.pid)
     x = str(k.name.decode('utf-8', 'replace'))
     f = open("other.txt", "a")
     f.write("PID: ")
     f.write(p)
     f.write("  \t")
     f.write("NAME: ")
     f.write(x)
     f.write("  \t")
     f.write("CPU: ")
     f.write(l)
     f.write("\n")
     f.close()
