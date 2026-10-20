# BSD syscall number and configuration index

[Dispatch and catalog guide](README.md)

Every declaration alternative in `bsd/kern/syscalls.master` appears below. Conditions preserve the preprocessor branches without selecting a product build. A reserved or disabled entry is not an available operation. Number 0 is the table's `nosys` entry, while architecture dispatch separately recognizes indirect syscall encoding.

| Number | Master declaration / implementation catalog | Condition | Reserved/disabled annotation |
| ---: | --- | --- | --- |
| 0 | [nosys](../../../xnu/bsd/kern/syscalls.master#L45) | `always` | indirect syscall |
| 1 | [exit](../../../xnu/bsd/kern/syscalls.master#L46) · [mechanism](processes-credentials-and-policy.md#1-exit) | `always` |  |
| 2 | [fork](../../../xnu/bsd/kern/syscalls.master#L47) · [mechanism](processes-credentials-and-policy.md#2-fork) | `always` |  |
| 3 | [read](../../../xnu/bsd/kern/syscalls.master#L48) · [mechanism](files-and-descriptors.md#3-read) | `always` |  |
| 4 | [write](../../../xnu/bsd/kern/syscalls.master#L49) · [mechanism](files-and-descriptors.md#4-write) | `always` |  |
| 5 | [open](../../../xnu/bsd/kern/syscalls.master#L50) · [mechanism](files-and-descriptors.md#5-open) | `always` |  |
| 6 | [sys_close](../../../xnu/bsd/kern/syscalls.master#L51) · [mechanism](files-and-descriptors.md#6-sys_close) | `always` |  |
| 7 | [wait4](../../../xnu/bsd/kern/syscalls.master#L52) · [mechanism](processes-credentials-and-policy.md#7-wait4) | `always` |  |
| 8 | [enosys](../../../xnu/bsd/kern/syscalls.master#L53) | `always` | old creat |
| 9 | [link](../../../xnu/bsd/kern/syscalls.master#L54) · [mechanism](filesystem-namespace.md#9-link) | `always` |  |
| 10 | [unlink](../../../xnu/bsd/kern/syscalls.master#L55) · [mechanism](filesystem-namespace.md#10-unlink) | `always` |  |
| 11 | [enosys](../../../xnu/bsd/kern/syscalls.master#L56) | `always` | old execv |
| 12 | [sys_chdir](../../../xnu/bsd/kern/syscalls.master#L57) · [mechanism](filesystem-namespace.md#12-sys_chdir) | `always` |  |
| 13 | [sys_fchdir](../../../xnu/bsd/kern/syscalls.master#L58) · [mechanism](filesystem-namespace.md#13-sys_fchdir) | `always` |  |
| 14 | [mknod](../../../xnu/bsd/kern/syscalls.master#L59) · [mechanism](filesystem-namespace.md#14-mknod) | `always` |  |
| 15 | [chmod](../../../xnu/bsd/kern/syscalls.master#L60) · [mechanism](filesystem-metadata.md#15-chmod) | `always` |  |
| 16 | [chown](../../../xnu/bsd/kern/syscalls.master#L61) · [mechanism](filesystem-metadata.md#16-chown) | `always` |  |
| 17 | [enosys](../../../xnu/bsd/kern/syscalls.master#L62) | `always` | old break |
| 18 | [getfsstat](../../../xnu/bsd/kern/syscalls.master#L63) · [mechanism](filesystem-mounts-and-control.md#18-getfsstat) | `always` |  |
| 19 | [enosys](../../../xnu/bsd/kern/syscalls.master#L64) | `always` | old lseek |
| 20 | [getpid](../../../xnu/bsd/kern/syscalls.master#L65) · [mechanism](processes-credentials-and-policy.md#20-getpid) | `always` |  |
| 21 | [enosys](../../../xnu/bsd/kern/syscalls.master#L66) | `always` | old mount |
| 22 | [enosys](../../../xnu/bsd/kern/syscalls.master#L67) | `always` | old umount |
| 23 | [setuid](../../../xnu/bsd/kern/syscalls.master#L68) · [mechanism](processes-credentials-and-policy.md#23-setuid) | `always` |  |
| 24 | [getuid](../../../xnu/bsd/kern/syscalls.master#L69) · [mechanism](processes-credentials-and-policy.md#24-getuid) | `always` |  |
| 25 | [geteuid](../../../xnu/bsd/kern/syscalls.master#L70) · [mechanism](processes-credentials-and-policy.md#25-geteuid) | `always` |  |
| 26 | [ptrace](../../../xnu/bsd/kern/syscalls.master#L71) · [mechanism](processes-credentials-and-policy.md#26-ptrace) | `always` |  |
| 27 | [recvmsg](../../../xnu/bsd/kern/syscalls.master#L73) · [mechanism](sockets-and-network-policy.md#27-recvmsg) | `(SOCKETS)` |  |
| 28 | [sendmsg](../../../xnu/bsd/kern/syscalls.master#L74) · [mechanism](sockets-and-network-policy.md#28-sendmsg) | `(SOCKETS)` |  |
| 29 | [recvfrom](../../../xnu/bsd/kern/syscalls.master#L75) · [mechanism](sockets-and-network-policy.md#29-recvfrom) | `(SOCKETS)` |  |
| 30 | [accept](../../../xnu/bsd/kern/syscalls.master#L76) · [mechanism](sockets-and-network-policy.md#30-accept) | `(SOCKETS)` |  |
| 31 | [getpeername](../../../xnu/bsd/kern/syscalls.master#L77) · [mechanism](sockets-and-network-policy.md#31-getpeername) | `(SOCKETS)` |  |
| 32 | [getsockname](../../../xnu/bsd/kern/syscalls.master#L78) · [mechanism](sockets-and-network-policy.md#32-getsockname) | `(SOCKETS)` |  |
| 27 | [nosys](../../../xnu/bsd/kern/syscalls.master#L80) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 28 | [nosys](../../../xnu/bsd/kern/syscalls.master#L81) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 29 | [nosys](../../../xnu/bsd/kern/syscalls.master#L82) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 30 | [nosys](../../../xnu/bsd/kern/syscalls.master#L83) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 31 | [nosys](../../../xnu/bsd/kern/syscalls.master#L84) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 32 | [nosys](../../../xnu/bsd/kern/syscalls.master#L85) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 33 | [access](../../../xnu/bsd/kern/syscalls.master#L87) · [mechanism](filesystem-metadata.md#33-access) | `always` |  |
| 34 | [chflags](../../../xnu/bsd/kern/syscalls.master#L88) · [mechanism](filesystem-metadata.md#34-chflags) | `always` |  |
| 35 | [fchflags](../../../xnu/bsd/kern/syscalls.master#L89) · [mechanism](filesystem-metadata.md#35-fchflags) | `always` |  |
| 36 | [sync](../../../xnu/bsd/kern/syscalls.master#L90) · [mechanism](filesystem-mounts-and-control.md#36-sync) | `always` |  |
| 37 | [kill](../../../xnu/bsd/kern/syscalls.master#L91) · [mechanism](signals-and-thread-control.md#37-kill) | `always` |  |
| 38 | [sys_crossarch_trap](../../../xnu/bsd/kern/syscalls.master#L92) · [mechanism](processes-credentials-and-policy.md#38-sys_crossarch_trap) | `always` |  |
| 39 | [getppid](../../../xnu/bsd/kern/syscalls.master#L93) · [mechanism](processes-credentials-and-policy.md#39-getppid) | `always` |  |
| 40 | [nosys](../../../xnu/bsd/kern/syscalls.master#L94) | `always` | old lstat |
| 41 | [sys_dup](../../../xnu/bsd/kern/syscalls.master#L95) · [mechanism](files-and-descriptors.md#41-sys_dup) | `always` |  |
| 42 | [pipe](../../../xnu/bsd/kern/syscalls.master#L96) · [mechanism](files-and-descriptors.md#42-pipe) | `always` |  |
| 43 | [getegid](../../../xnu/bsd/kern/syscalls.master#L97) · [mechanism](processes-credentials-and-policy.md#43-getegid) | `always` |  |
| 44 | [nosys](../../../xnu/bsd/kern/syscalls.master#L98) | `always` | old profil |
| 45 | [nosys](../../../xnu/bsd/kern/syscalls.master#L99) | `always` | old ktrace |
| 46 | [sigaction](../../../xnu/bsd/kern/syscalls.master#L100) · [mechanism](signals-and-thread-control.md#46-sigaction) | `always` |  |
| 47 | [getgid](../../../xnu/bsd/kern/syscalls.master#L101) · [mechanism](processes-credentials-and-policy.md#47-getgid) | `always` |  |
| 48 | [sigprocmask](../../../xnu/bsd/kern/syscalls.master#L102) · [mechanism](signals-and-thread-control.md#48-sigprocmask) | `always` |  |
| 49 | [getlogin](../../../xnu/bsd/kern/syscalls.master#L103) · [mechanism](processes-credentials-and-policy.md#49-getlogin) | `always` |  |
| 50 | [setlogin](../../../xnu/bsd/kern/syscalls.master#L104) · [mechanism](processes-credentials-and-policy.md#50-setlogin) | `always` |  |
| 51 | [acct](../../../xnu/bsd/kern/syscalls.master#L105) · [mechanism](time-and-accounting.md#51-acct) | `always` |  |
| 52 | [sigpending](../../../xnu/bsd/kern/syscalls.master#L106) · [mechanism](signals-and-thread-control.md#52-sigpending) | `always` |  |
| 53 | [sigaltstack](../../../xnu/bsd/kern/syscalls.master#L107) · [mechanism](signals-and-thread-control.md#53-sigaltstack) | `always` |  |
| 54 | [ioctl](../../../xnu/bsd/kern/syscalls.master#L108) · [mechanism](files-and-descriptors.md#54-ioctl) | `always` |  |
| 55 | [reboot](../../../xnu/bsd/kern/syscalls.master#L109) · [mechanism](processes-credentials-and-policy.md#55-reboot) | `always` |  |
| 56 | [revoke](../../../xnu/bsd/kern/syscalls.master#L110) · [mechanism](filesystem-namespace.md#56-revoke) | `always` |  |
| 57 | [symlink](../../../xnu/bsd/kern/syscalls.master#L111) · [mechanism](filesystem-namespace.md#57-symlink) | `always` |  |
| 58 | [readlink](../../../xnu/bsd/kern/syscalls.master#L112) · [mechanism](filesystem-namespace.md#58-readlink) | `always` |  |
| 59 | [execve](../../../xnu/bsd/kern/syscalls.master#L113) · [mechanism](processes-credentials-and-policy.md#59-execve) | `always` |  |
| 60 | [umask](../../../xnu/bsd/kern/syscalls.master#L114) · [mechanism](filesystem-metadata.md#60-umask) | `always` |  |
| 61 | [chroot](../../../xnu/bsd/kern/syscalls.master#L115) · [mechanism](filesystem-namespace.md#61-chroot) | `always` |  |
| 62 | [nosys](../../../xnu/bsd/kern/syscalls.master#L116) | `always` | old fstat |
| 63 | [nosys](../../../xnu/bsd/kern/syscalls.master#L117) | `always` | used internally and reserved |
| 64 | [nosys](../../../xnu/bsd/kern/syscalls.master#L118) | `always` | old getpagesize |
| 65 | [msync](../../../xnu/bsd/kern/syscalls.master#L119) · [mechanism](virtual-memory.md#65-msync) | `always` |  |
| 66 | [vfork](../../../xnu/bsd/kern/syscalls.master#L121) · [mechanism](processes-credentials-and-policy.md#66-vfork) | `(CONFIG_VFORK)` |  |
| 66 | [nosys](../../../xnu/bsd/kern/syscalls.master#L123) | `(!(CONFIG_VFORK))` | old vfork |
| 67 | [oslog_coproc_reg](../../../xnu/bsd/kern/syscalls.master#L125) · [mechanism](diagnostics-and-system-control.md#67-oslog_coproc_reg) | `always` |  |
| 68 | [oslog_coproc](../../../xnu/bsd/kern/syscalls.master#L126) · [mechanism](diagnostics-and-system-control.md#68-oslog_coproc) | `always` |  |
| 69 | [nosys](../../../xnu/bsd/kern/syscalls.master#L127) | `always` | old sbrk |
| 70 | [nosys](../../../xnu/bsd/kern/syscalls.master#L128) | `always` | old sstk |
| 71 | [nosys](../../../xnu/bsd/kern/syscalls.master#L129) | `always` | old mmap |
| 72 | [nosys](../../../xnu/bsd/kern/syscalls.master#L130) | `always` | old vadvise |
| 73 | [munmap](../../../xnu/bsd/kern/syscalls.master#L131) · [mechanism](virtual-memory.md#73-munmap) | `always` |  |
| 74 | [mprotect](../../../xnu/bsd/kern/syscalls.master#L132) · [mechanism](virtual-memory.md#74-mprotect) | `always` |  |
| 75 | [madvise](../../../xnu/bsd/kern/syscalls.master#L133) · [mechanism](virtual-memory.md#75-madvise) | `always` |  |
| 76 | [nosys](../../../xnu/bsd/kern/syscalls.master#L134) | `always` | old vhangup |
| 77 | [nosys](../../../xnu/bsd/kern/syscalls.master#L135) | `always` | old vlimit |
| 78 | [mincore](../../../xnu/bsd/kern/syscalls.master#L136) · [mechanism](virtual-memory.md#78-mincore) | `always` |  |
| 79 | [getgroups](../../../xnu/bsd/kern/syscalls.master#L137) · [mechanism](processes-credentials-and-policy.md#79-getgroups) | `always` |  |
| 80 | [setgroups](../../../xnu/bsd/kern/syscalls.master#L138) · [mechanism](processes-credentials-and-policy.md#80-setgroups) | `always` |  |
| 81 | [getpgrp](../../../xnu/bsd/kern/syscalls.master#L139) · [mechanism](processes-credentials-and-policy.md#81-getpgrp) | `always` |  |
| 82 | [setpgid](../../../xnu/bsd/kern/syscalls.master#L140) · [mechanism](processes-credentials-and-policy.md#82-setpgid) | `always` |  |
| 83 | [setitimer](../../../xnu/bsd/kern/syscalls.master#L141) · [mechanism](time-and-accounting.md#83-setitimer) | `always` |  |
| 84 | [nosys](../../../xnu/bsd/kern/syscalls.master#L142) | `always` | old wait |
| 85 | [swapon](../../../xnu/bsd/kern/syscalls.master#L143) · [mechanism](virtual-memory.md#85-swapon) | `always` |  |
| 86 | [getitimer](../../../xnu/bsd/kern/syscalls.master#L144) · [mechanism](time-and-accounting.md#86-getitimer) | `always` |  |
| 87 | [nosys](../../../xnu/bsd/kern/syscalls.master#L145) | `always` | old gethostname |
| 88 | [nosys](../../../xnu/bsd/kern/syscalls.master#L146) | `always` | old sethostname |
| 89 | [sys_getdtablesize](../../../xnu/bsd/kern/syscalls.master#L147) · [mechanism](files-and-descriptors.md#89-sys_getdtablesize) | `always` |  |
| 90 | [sys_dup2](../../../xnu/bsd/kern/syscalls.master#L148) · [mechanism](files-and-descriptors.md#90-sys_dup2) | `always` |  |
| 91 | [nosys](../../../xnu/bsd/kern/syscalls.master#L149) | `always` | old getdopt |
| 92 | [sys_fcntl](../../../xnu/bsd/kern/syscalls.master#L150) · [mechanism](files-and-descriptors.md#92-sys_fcntl) | `always` |  |
| 93 | [select](../../../xnu/bsd/kern/syscalls.master#L151) · [mechanism](events-pthreads-and-async-io.md#93-select) | `always` |  |
| 94 | [nosys](../../../xnu/bsd/kern/syscalls.master#L152) | `always` | old setdopt |
| 95 | [fsync](../../../xnu/bsd/kern/syscalls.master#L153) · [mechanism](filesystem-mounts-and-control.md#95-fsync) | `always` |  |
| 96 | [setpriority](../../../xnu/bsd/kern/syscalls.master#L154) · [mechanism](processes-credentials-and-policy.md#96-setpriority) | `always` |  |
| 97 | [socket](../../../xnu/bsd/kern/syscalls.master#L156) · [mechanism](sockets-and-network-policy.md#97-socket) | `(SOCKETS)` |  |
| 98 | [connect](../../../xnu/bsd/kern/syscalls.master#L157) · [mechanism](sockets-and-network-policy.md#98-connect) | `(SOCKETS)` |  |
| 97 | [nosys](../../../xnu/bsd/kern/syscalls.master#L159) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 98 | [nosys](../../../xnu/bsd/kern/syscalls.master#L160) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 99 | [nosys](../../../xnu/bsd/kern/syscalls.master#L162) | `always` | old accept |
| 100 | [getpriority](../../../xnu/bsd/kern/syscalls.master#L163) · [mechanism](processes-credentials-and-policy.md#100-getpriority) | `always` |  |
| 101 | [nosys](../../../xnu/bsd/kern/syscalls.master#L164) | `always` | old send |
| 102 | [nosys](../../../xnu/bsd/kern/syscalls.master#L165) | `always` | old recv |
| 103 | [nosys](../../../xnu/bsd/kern/syscalls.master#L166) | `always` | old sigreturn |
| 104 | [bind](../../../xnu/bsd/kern/syscalls.master#L168) · [mechanism](sockets-and-network-policy.md#104-bind) | `(SOCKETS)` |  |
| 105 | [setsockopt](../../../xnu/bsd/kern/syscalls.master#L169) · [mechanism](sockets-and-network-policy.md#105-setsockopt) | `(SOCKETS)` |  |
| 106 | [listen](../../../xnu/bsd/kern/syscalls.master#L170) · [mechanism](sockets-and-network-policy.md#106-listen) | `(SOCKETS)` |  |
| 104 | [nosys](../../../xnu/bsd/kern/syscalls.master#L172) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 105 | [nosys](../../../xnu/bsd/kern/syscalls.master#L173) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 106 | [nosys](../../../xnu/bsd/kern/syscalls.master#L174) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 107 | [nosys](../../../xnu/bsd/kern/syscalls.master#L176) | `always` | old vtimes |
| 108 | [nosys](../../../xnu/bsd/kern/syscalls.master#L177) | `always` | old sigvec |
| 109 | [nosys](../../../xnu/bsd/kern/syscalls.master#L178) | `always` | old sigblock |
| 110 | [nosys](../../../xnu/bsd/kern/syscalls.master#L179) | `always` | old sigsetmask |
| 111 | [sigsuspend](../../../xnu/bsd/kern/syscalls.master#L180) · [mechanism](signals-and-thread-control.md#111-sigsuspend) | `always` |  |
| 112 | [nosys](../../../xnu/bsd/kern/syscalls.master#L181) | `always` | old sigstack |
| 113 | [nosys](../../../xnu/bsd/kern/syscalls.master#L183) | `(SOCKETS)` | old recvmsg |
| 114 | [nosys](../../../xnu/bsd/kern/syscalls.master#L184) | `(SOCKETS)` | old sendmsg |
| 113 | [nosys](../../../xnu/bsd/kern/syscalls.master#L186) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 114 | [nosys](../../../xnu/bsd/kern/syscalls.master#L187) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 115 | [nosys](../../../xnu/bsd/kern/syscalls.master#L189) | `always` | old vtrace |
| 116 | [gettimeofday](../../../xnu/bsd/kern/syscalls.master#L190) · [mechanism](time-and-accounting.md#116-gettimeofday) | `always` |  |
| 117 | [getrusage](../../../xnu/bsd/kern/syscalls.master#L191) · [mechanism](processes-credentials-and-policy.md#117-getrusage) | `always` |  |
| 118 | [getsockopt](../../../xnu/bsd/kern/syscalls.master#L193) · [mechanism](sockets-and-network-policy.md#118-getsockopt) | `(SOCKETS)` |  |
| 118 | [nosys](../../../xnu/bsd/kern/syscalls.master#L195) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 119 | [nosys](../../../xnu/bsd/kern/syscalls.master#L197) | `always` | old resuba |
| 120 | [readv](../../../xnu/bsd/kern/syscalls.master#L198) · [mechanism](files-and-descriptors.md#120-readv) | `always` |  |
| 121 | [writev](../../../xnu/bsd/kern/syscalls.master#L199) · [mechanism](files-and-descriptors.md#121-writev) | `always` |  |
| 122 | [settimeofday](../../../xnu/bsd/kern/syscalls.master#L200) · [mechanism](time-and-accounting.md#122-settimeofday) | `always` |  |
| 123 | [fchown](../../../xnu/bsd/kern/syscalls.master#L201) · [mechanism](filesystem-metadata.md#123-fchown) | `always` |  |
| 124 | [fchmod](../../../xnu/bsd/kern/syscalls.master#L202) · [mechanism](filesystem-metadata.md#124-fchmod) | `always` |  |
| 125 | [nosys](../../../xnu/bsd/kern/syscalls.master#L203) | `always` | old recvfrom |
| 126 | [setreuid](../../../xnu/bsd/kern/syscalls.master#L204) · [mechanism](processes-credentials-and-policy.md#126-setreuid) | `always` |  |
| 127 | [setregid](../../../xnu/bsd/kern/syscalls.master#L205) · [mechanism](processes-credentials-and-policy.md#127-setregid) | `always` |  |
| 128 | [rename](../../../xnu/bsd/kern/syscalls.master#L206) · [mechanism](filesystem-namespace.md#128-rename) | `always` |  |
| 129 | [nosys](../../../xnu/bsd/kern/syscalls.master#L207) | `always` | old truncate |
| 130 | [nosys](../../../xnu/bsd/kern/syscalls.master#L208) | `always` | old ftruncate |
| 131 | [sys_flock](../../../xnu/bsd/kern/syscalls.master#L209) · [mechanism](files-and-descriptors.md#131-sys_flock) | `always` |  |
| 132 | [mkfifo](../../../xnu/bsd/kern/syscalls.master#L210) · [mechanism](filesystem-namespace.md#132-mkfifo) | `always` |  |
| 133 | [sendto](../../../xnu/bsd/kern/syscalls.master#L212) · [mechanism](sockets-and-network-policy.md#133-sendto) | `(SOCKETS)` |  |
| 134 | [shutdown](../../../xnu/bsd/kern/syscalls.master#L213) · [mechanism](sockets-and-network-policy.md#134-shutdown) | `(SOCKETS)` |  |
| 135 | [socketpair](../../../xnu/bsd/kern/syscalls.master#L214) · [mechanism](sockets-and-network-policy.md#135-socketpair) | `(SOCKETS)` |  |
| 133 | [nosys](../../../xnu/bsd/kern/syscalls.master#L216) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 134 | [nosys](../../../xnu/bsd/kern/syscalls.master#L217) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 135 | [nosys](../../../xnu/bsd/kern/syscalls.master#L218) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 136 | [mkdir](../../../xnu/bsd/kern/syscalls.master#L220) · [mechanism](filesystem-namespace.md#136-mkdir) | `always` |  |
| 137 | [rmdir](../../../xnu/bsd/kern/syscalls.master#L221) · [mechanism](filesystem-namespace.md#137-rmdir) | `always` |  |
| 138 | [utimes](../../../xnu/bsd/kern/syscalls.master#L222) · [mechanism](filesystem-metadata.md#138-utimes) | `always` |  |
| 139 | [futimes](../../../xnu/bsd/kern/syscalls.master#L223) · [mechanism](filesystem-metadata.md#139-futimes) | `always` |  |
| 140 | [adjtime](../../../xnu/bsd/kern/syscalls.master#L224) · [mechanism](time-and-accounting.md#140-adjtime) | `always` |  |
| 141 | [nosys](../../../xnu/bsd/kern/syscalls.master#L225) | `always` | old getpeername |
| 142 | [gethostuuid](../../../xnu/bsd/kern/syscalls.master#L226) · [mechanism](diagnostics-and-system-control.md#142-gethostuuid) | `always` |  |
| 143 | [nosys](../../../xnu/bsd/kern/syscalls.master#L227) | `always` | old sethostid |
| 144 | [nosys](../../../xnu/bsd/kern/syscalls.master#L228) | `always` | old getrlimit |
| 145 | [nosys](../../../xnu/bsd/kern/syscalls.master#L229) | `always` | old setrlimit |
| 146 | [nosys](../../../xnu/bsd/kern/syscalls.master#L230) | `always` | old killpg |
| 147 | [setsid](../../../xnu/bsd/kern/syscalls.master#L231) · [mechanism](processes-credentials-and-policy.md#147-setsid) | `always` |  |
| 148 | [nosys](../../../xnu/bsd/kern/syscalls.master#L232) | `always` | old setquota |
| 149 | [nosys](../../../xnu/bsd/kern/syscalls.master#L233) | `always` | old qquota |
| 150 | [nosys](../../../xnu/bsd/kern/syscalls.master#L234) | `always` | old getsockname |
| 151 | [getpgid](../../../xnu/bsd/kern/syscalls.master#L235) · [mechanism](processes-credentials-and-policy.md#151-getpgid) | `always` |  |
| 152 | [setprivexec](../../../xnu/bsd/kern/syscalls.master#L236) · [mechanism](processes-credentials-and-policy.md#152-setprivexec) | `always` |  |
| 153 | [pread](../../../xnu/bsd/kern/syscalls.master#L237) · [mechanism](files-and-descriptors.md#153-pread) | `always` |  |
| 154 | [pwrite](../../../xnu/bsd/kern/syscalls.master#L238) · [mechanism](files-and-descriptors.md#154-pwrite) | `always` |  |
| 155 | [nfssvc](../../../xnu/bsd/kern/syscalls.master#L241) · [mechanism](filesystem-mounts-and-control.md#155-nfssvc) | `(NFSSERVER)` |  |
| 155 | [nosys](../../../xnu/bsd/kern/syscalls.master#L243) | `(!(NFSSERVER))` | Unavailable/reserved implementation (`nosys`). |
| 156 | [nosys](../../../xnu/bsd/kern/syscalls.master#L246) | `always` | old getdirentries |
| 157 | [statfs](../../../xnu/bsd/kern/syscalls.master#L247) · [mechanism](filesystem-mounts-and-control.md#157-statfs) | `always` |  |
| 158 | [fstatfs](../../../xnu/bsd/kern/syscalls.master#L248) · [mechanism](filesystem-mounts-and-control.md#158-fstatfs) | `always` |  |
| 159 | [unmount](../../../xnu/bsd/kern/syscalls.master#L249) · [mechanism](filesystem-mounts-and-control.md#159-unmount) | `always` |  |
| 160 | [nosys](../../../xnu/bsd/kern/syscalls.master#L250) | `always` | old async_daemon |
| 161 | [getfh](../../../xnu/bsd/kern/syscalls.master#L253) · [mechanism](filesystem-mounts-and-control.md#161-getfh) | `(NFSSERVER)` |  |
| 161 | [nosys](../../../xnu/bsd/kern/syscalls.master#L255) | `(!(NFSSERVER))` | Unavailable/reserved implementation (`nosys`). |
| 162 | [nosys](../../../xnu/bsd/kern/syscalls.master#L258) | `always` | old getdomainname |
| 163 | [nosys](../../../xnu/bsd/kern/syscalls.master#L259) | `always` | old setdomainname |
| 164 | [funmount](../../../xnu/bsd/kern/syscalls.master#L260) · [mechanism](filesystem-mounts-and-control.md#164-funmount) | `always` |  |
| 165 | [quotactl](../../../xnu/bsd/kern/syscalls.master#L261) · [mechanism](filesystem-mounts-and-control.md#165-quotactl) | `always` |  |
| 166 | [nosys](../../../xnu/bsd/kern/syscalls.master#L262) | `always` | old exportfs |
| 167 | [mount](../../../xnu/bsd/kern/syscalls.master#L263) · [mechanism](filesystem-mounts-and-control.md#167-mount) | `always` |  |
| 168 | [nosys](../../../xnu/bsd/kern/syscalls.master#L264) | `always` | old ustat |
| 169 | [csops](../../../xnu/bsd/kern/syscalls.master#L265) · [mechanism](security-and-audit.md#169-csops) | `always` |  |
| 170 | [csops_audittoken](../../../xnu/bsd/kern/syscalls.master#L266) · [mechanism](security-and-audit.md#170-csops_audittoken) | `always` |  |
| 171 | [nosys](../../../xnu/bsd/kern/syscalls.master#L267) | `always` | old wait3 |
| 172 | [nosys](../../../xnu/bsd/kern/syscalls.master#L268) | `always` | old rpause |
| 173 | [waitid](../../../xnu/bsd/kern/syscalls.master#L269) · [mechanism](processes-credentials-and-policy.md#173-waitid) | `always` |  |
| 174 | [nosys](../../../xnu/bsd/kern/syscalls.master#L270) | `always` | old getdents |
| 175 | [nosys](../../../xnu/bsd/kern/syscalls.master#L271) | `always` | old gc_control |
| 176 | [nosys](../../../xnu/bsd/kern/syscalls.master#L272) | `always` | old add_profil |
| 177 | [kdebug_typefilter](../../../xnu/bsd/kern/syscalls.master#L273) · [mechanism](diagnostics-and-system-control.md#177-kdebug_typefilter) | `always` |  |
| 178 | [kdebug_trace_string](../../../xnu/bsd/kern/syscalls.master#L274) · [mechanism](diagnostics-and-system-control.md#178-kdebug_trace_string) | `always` |  |
| 179 | [kdebug_trace64](../../../xnu/bsd/kern/syscalls.master#L275) · [mechanism](diagnostics-and-system-control.md#179-kdebug_trace64) | `always` |  |
| 180 | [kdebug_trace](../../../xnu/bsd/kern/syscalls.master#L276) · [mechanism](diagnostics-and-system-control.md#180-kdebug_trace) | `always` |  |
| 181 | [setgid](../../../xnu/bsd/kern/syscalls.master#L277) · [mechanism](processes-credentials-and-policy.md#181-setgid) | `always` |  |
| 182 | [setegid](../../../xnu/bsd/kern/syscalls.master#L278) · [mechanism](processes-credentials-and-policy.md#182-setegid) | `always` |  |
| 183 | [seteuid](../../../xnu/bsd/kern/syscalls.master#L279) · [mechanism](processes-credentials-and-policy.md#183-seteuid) | `always` |  |
| 184 | [sigreturn](../../../xnu/bsd/kern/syscalls.master#L280) · [mechanism](signals-and-thread-control.md#184-sigreturn) | `always` |  |
| 185 | [sys_panic_with_data](../../../xnu/bsd/kern/syscalls.master#L281) · [mechanism](diagnostics-and-system-control.md#185-sys_panic_with_data) | `always` |  |
| 186 | [thread_selfcounts](../../../xnu/bsd/kern/syscalls.master#L282) · [mechanism](time-and-accounting.md#186-thread_selfcounts) | `always` |  |
| 187 | [fdatasync](../../../xnu/bsd/kern/syscalls.master#L283) · [mechanism](filesystem-mounts-and-control.md#187-fdatasync) | `always` |  |
| 188 | [stat](../../../xnu/bsd/kern/syscalls.master#L284) · [mechanism](filesystem-metadata.md#188-stat) | `always` |  |
| 189 | [sys_fstat](../../../xnu/bsd/kern/syscalls.master#L285) · [mechanism](filesystem-metadata.md#189-sys_fstat) | `always` |  |
| 190 | [lstat](../../../xnu/bsd/kern/syscalls.master#L286) · [mechanism](filesystem-metadata.md#190-lstat) | `always` |  |
| 191 | [pathconf](../../../xnu/bsd/kern/syscalls.master#L287) · [mechanism](filesystem-metadata.md#191-pathconf) | `always` |  |
| 192 | [sys_fpathconf](../../../xnu/bsd/kern/syscalls.master#L288) · [mechanism](filesystem-metadata.md#192-sys_fpathconf) | `always` |  |
| 193 | [nosys](../../../xnu/bsd/kern/syscalls.master#L289) | `always` | old getfsstat |
| 194 | [getrlimit](../../../xnu/bsd/kern/syscalls.master#L290) · [mechanism](processes-credentials-and-policy.md#194-getrlimit) | `always` |  |
| 195 | [setrlimit](../../../xnu/bsd/kern/syscalls.master#L291) · [mechanism](processes-credentials-and-policy.md#195-setrlimit) | `always` |  |
| 196 | [getdirentries](../../../xnu/bsd/kern/syscalls.master#L292) · [mechanism](filesystem-metadata.md#196-getdirentries) | `always` |  |
| 197 | [mmap](../../../xnu/bsd/kern/syscalls.master#L293) · [mechanism](virtual-memory.md#197-mmap) | `always` |  |
| 198 | [nosys](../../../xnu/bsd/kern/syscalls.master#L294) | `always` | old __syscall |
| 199 | [lseek](../../../xnu/bsd/kern/syscalls.master#L295) · [mechanism](files-and-descriptors.md#199-lseek) | `always` |  |
| 200 | [truncate](../../../xnu/bsd/kern/syscalls.master#L296) · [mechanism](filesystem-metadata.md#200-truncate) | `always` |  |
| 201 | [ftruncate](../../../xnu/bsd/kern/syscalls.master#L297) · [mechanism](filesystem-metadata.md#201-ftruncate) | `always` |  |
| 202 | [sysctl](../../../xnu/bsd/kern/syscalls.master#L298) · [mechanism](diagnostics-and-system-control.md#202-sysctl) | `always` |  |
| 203 | [mlock](../../../xnu/bsd/kern/syscalls.master#L299) · [mechanism](virtual-memory.md#203-mlock) | `always` |  |
| 204 | [munlock](../../../xnu/bsd/kern/syscalls.master#L300) · [mechanism](virtual-memory.md#204-munlock) | `always` |  |
| 205 | [undelete](../../../xnu/bsd/kern/syscalls.master#L301) · [mechanism](filesystem-namespace.md#205-undelete) | `always` |  |
| 206 | [nosys](../../../xnu/bsd/kern/syscalls.master#L303) | `always` | old ATsocket |
| 207 | [nosys](../../../xnu/bsd/kern/syscalls.master#L304) | `always` | old ATgetmsg |
| 208 | [nosys](../../../xnu/bsd/kern/syscalls.master#L305) | `always` | old ATputmsg |
| 209 | [nosys](../../../xnu/bsd/kern/syscalls.master#L306) | `always` | old ATsndreq |
| 210 | [nosys](../../../xnu/bsd/kern/syscalls.master#L307) | `always` | old ATsndrsp |
| 211 | [nosys](../../../xnu/bsd/kern/syscalls.master#L308) | `always` | old ATgetreq |
| 212 | [nosys](../../../xnu/bsd/kern/syscalls.master#L309) | `always` | old ATgetrsp |
| 213 | [nosys](../../../xnu/bsd/kern/syscalls.master#L310) | `always` | Reserved for AppleTalk |
| 214 | [nosys](../../../xnu/bsd/kern/syscalls.master#L312) | `always` | Unavailable/reserved implementation (`nosys`). |
| 215 | [nosys](../../../xnu/bsd/kern/syscalls.master#L313) | `always` | Unavailable/reserved implementation (`nosys`). |
| 216 | [open_dprotected_np](../../../xnu/bsd/kern/syscalls.master#L324) · [mechanism](files-and-descriptors.md#216-open_dprotected_np) | `always` |  |
| 217 | [fsgetpath_ext](../../../xnu/bsd/kern/syscalls.master#L325) · [mechanism](filesystem-metadata.md#217-fsgetpath_ext) | `always` |  |
| 218 | [openat_dprotected_np](../../../xnu/bsd/kern/syscalls.master#L326) · [mechanism](files-and-descriptors.md#218-openat_dprotected_np) | `always` |  |
| 219 | [nosys](../../../xnu/bsd/kern/syscalls.master#L327) | `always` | old fstatv |
| 220 | [getattrlist](../../../xnu/bsd/kern/syscalls.master#L328) · [mechanism](filesystem-metadata.md#220-getattrlist) | `always` |  |
| 221 | [setattrlist](../../../xnu/bsd/kern/syscalls.master#L329) · [mechanism](filesystem-metadata.md#221-setattrlist) | `always` |  |
| 222 | [getdirentriesattr](../../../xnu/bsd/kern/syscalls.master#L330) · [mechanism](filesystem-metadata.md#222-getdirentriesattr) | `always` |  |
| 223 | [exchangedata](../../../xnu/bsd/kern/syscalls.master#L331) · [mechanism](filesystem-namespace.md#223-exchangedata) | `always` |  |
| 224 | [nosys](../../../xnu/bsd/kern/syscalls.master#L332) | `always` | old checkuseraccess or fsgetpath |
| 225 | [searchfs](../../../xnu/bsd/kern/syscalls.master#L333) · [mechanism](filesystem-metadata.md#225-searchfs) | `always` |  |
| 226 | [delete](../../../xnu/bsd/kern/syscalls.master#L334) · [mechanism](filesystem-namespace.md#226-delete) | `always` | private delete (Carbon semantics) |
| 227 | [copyfile](../../../xnu/bsd/kern/syscalls.master#L335) · [mechanism](filesystem-namespace.md#227-copyfile) | `always` |  |
| 228 | [fgetattrlist](../../../xnu/bsd/kern/syscalls.master#L336) · [mechanism](filesystem-metadata.md#228-fgetattrlist) | `always` |  |
| 229 | [fsetattrlist](../../../xnu/bsd/kern/syscalls.master#L337) · [mechanism](filesystem-metadata.md#229-fsetattrlist) | `always` |  |
| 230 | [poll](../../../xnu/bsd/kern/syscalls.master#L338) · [mechanism](events-pthreads-and-async-io.md#230-poll) | `always` |  |
| 231 | [nosys](../../../xnu/bsd/kern/syscalls.master#L339) | `always` | old watchevent |
| 232 | [nosys](../../../xnu/bsd/kern/syscalls.master#L340) | `always` | old waitevent |
| 233 | [nosys](../../../xnu/bsd/kern/syscalls.master#L341) | `always` | old modwatch |
| 234 | [getxattr](../../../xnu/bsd/kern/syscalls.master#L342) · [mechanism](filesystem-metadata.md#234-getxattr) | `always` |  |
| 235 | [fgetxattr](../../../xnu/bsd/kern/syscalls.master#L343) · [mechanism](filesystem-metadata.md#235-fgetxattr) | `always` |  |
| 236 | [setxattr](../../../xnu/bsd/kern/syscalls.master#L344) · [mechanism](filesystem-metadata.md#236-setxattr) | `always` |  |
| 237 | [fsetxattr](../../../xnu/bsd/kern/syscalls.master#L345) · [mechanism](filesystem-metadata.md#237-fsetxattr) | `always` |  |
| 238 | [removexattr](../../../xnu/bsd/kern/syscalls.master#L346) · [mechanism](filesystem-metadata.md#238-removexattr) | `always` |  |
| 239 | [fremovexattr](../../../xnu/bsd/kern/syscalls.master#L347) · [mechanism](filesystem-metadata.md#239-fremovexattr) | `always` |  |
| 240 | [listxattr](../../../xnu/bsd/kern/syscalls.master#L348) · [mechanism](filesystem-metadata.md#240-listxattr) | `always` |  |
| 241 | [flistxattr](../../../xnu/bsd/kern/syscalls.master#L349) · [mechanism](filesystem-metadata.md#241-flistxattr) | `always` |  |
| 242 | [fsctl](../../../xnu/bsd/kern/syscalls.master#L350) · [mechanism](filesystem-mounts-and-control.md#242-fsctl) | `always` |  |
| 243 | [initgroups](../../../xnu/bsd/kern/syscalls.master#L351) · [mechanism](processes-credentials-and-policy.md#243-initgroups) | `always` |  |
| 244 | [posix_spawn](../../../xnu/bsd/kern/syscalls.master#L352) · [mechanism](processes-credentials-and-policy.md#244-posix_spawn) | `always` |  |
| 245 | [ffsctl](../../../xnu/bsd/kern/syscalls.master#L353) · [mechanism](filesystem-mounts-and-control.md#245-ffsctl) | `always` |  |
| 246 | [nosys](../../../xnu/bsd/kern/syscalls.master#L354) | `always` | Unavailable/reserved implementation (`nosys`). |
| 247 | [nosys](../../../xnu/bsd/kern/syscalls.master#L355) | `always` | old nfsclnt |
| 248 | [fhopen](../../../xnu/bsd/kern/syscalls.master#L358) · [mechanism](filesystem-mounts-and-control.md#248-fhopen) | `(NFSSERVER)` |  |
| 248 | [nosys](../../../xnu/bsd/kern/syscalls.master#L360) | `(!(NFSSERVER))` | Unavailable/reserved implementation (`nosys`). |
| 249 | [nosys](../../../xnu/bsd/kern/syscalls.master#L363) | `always` | Unavailable/reserved implementation (`nosys`). |
| 250 | [minherit](../../../xnu/bsd/kern/syscalls.master#L364) · [mechanism](virtual-memory.md#250-minherit) | `always` |  |
| 251 | [semsys](../../../xnu/bsd/kern/syscalls.master#L366) · [mechanism](local-ipc.md#251-semsys) | `(SYSV_SEM)` |  |
| 251 | [nosys](../../../xnu/bsd/kern/syscalls.master#L368) | `(!(SYSV_SEM))` | Unavailable/reserved implementation (`nosys`). |
| 252 | [msgsys](../../../xnu/bsd/kern/syscalls.master#L371) · [mechanism](local-ipc.md#252-msgsys) | `(SYSV_MSG)` |  |
| 252 | [nosys](../../../xnu/bsd/kern/syscalls.master#L373) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 253 | [shmsys](../../../xnu/bsd/kern/syscalls.master#L376) · [mechanism](local-ipc.md#253-shmsys) | `(SYSV_SHM)` |  |
| 253 | [nosys](../../../xnu/bsd/kern/syscalls.master#L378) | `(!(SYSV_SHM))` | Unavailable/reserved implementation (`nosys`). |
| 254 | [semctl](../../../xnu/bsd/kern/syscalls.master#L381) · [mechanism](local-ipc.md#254-semctl) | `(SYSV_SEM)` |  |
| 255 | [semget](../../../xnu/bsd/kern/syscalls.master#L382) · [mechanism](local-ipc.md#255-semget) | `(SYSV_SEM)` |  |
| 256 | [semop](../../../xnu/bsd/kern/syscalls.master#L383) · [mechanism](local-ipc.md#256-semop) | `(SYSV_SEM)` |  |
| 257 | [nosys](../../../xnu/bsd/kern/syscalls.master#L384) | `(SYSV_SEM)` | old semconfig |
| 254 | [nosys](../../../xnu/bsd/kern/syscalls.master#L386) | `(!(SYSV_SEM))` | Unavailable/reserved implementation (`nosys`). |
| 255 | [nosys](../../../xnu/bsd/kern/syscalls.master#L387) | `(!(SYSV_SEM))` | Unavailable/reserved implementation (`nosys`). |
| 256 | [nosys](../../../xnu/bsd/kern/syscalls.master#L388) | `(!(SYSV_SEM))` | Unavailable/reserved implementation (`nosys`). |
| 257 | [nosys](../../../xnu/bsd/kern/syscalls.master#L389) | `(!(SYSV_SEM))` | Unavailable/reserved implementation (`nosys`). |
| 258 | [msgctl](../../../xnu/bsd/kern/syscalls.master#L392) · [mechanism](local-ipc.md#258-msgctl) | `(SYSV_MSG)` |  |
| 259 | [msgget](../../../xnu/bsd/kern/syscalls.master#L393) · [mechanism](local-ipc.md#259-msgget) | `(SYSV_MSG)` |  |
| 260 | [msgsnd](../../../xnu/bsd/kern/syscalls.master#L394) · [mechanism](local-ipc.md#260-msgsnd) | `(SYSV_MSG)` |  |
| 261 | [msgrcv](../../../xnu/bsd/kern/syscalls.master#L395) · [mechanism](local-ipc.md#261-msgrcv) | `(SYSV_MSG)` |  |
| 258 | [nosys](../../../xnu/bsd/kern/syscalls.master#L397) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 259 | [nosys](../../../xnu/bsd/kern/syscalls.master#L398) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 260 | [nosys](../../../xnu/bsd/kern/syscalls.master#L399) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 261 | [nosys](../../../xnu/bsd/kern/syscalls.master#L400) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 262 | [shmat](../../../xnu/bsd/kern/syscalls.master#L403) · [mechanism](local-ipc.md#262-shmat) | `(SYSV_SHM)` |  |
| 263 | [shmctl](../../../xnu/bsd/kern/syscalls.master#L404) · [mechanism](local-ipc.md#263-shmctl) | `(SYSV_SHM)` |  |
| 264 | [shmdt](../../../xnu/bsd/kern/syscalls.master#L405) · [mechanism](local-ipc.md#264-shmdt) | `(SYSV_SHM)` |  |
| 265 | [shmget](../../../xnu/bsd/kern/syscalls.master#L406) · [mechanism](local-ipc.md#265-shmget) | `(SYSV_SHM)` |  |
| 262 | [nosys](../../../xnu/bsd/kern/syscalls.master#L408) | `(!(SYSV_SHM))` | Unavailable/reserved implementation (`nosys`). |
| 263 | [nosys](../../../xnu/bsd/kern/syscalls.master#L409) | `(!(SYSV_SHM))` | Unavailable/reserved implementation (`nosys`). |
| 264 | [nosys](../../../xnu/bsd/kern/syscalls.master#L410) | `(!(SYSV_SHM))` | Unavailable/reserved implementation (`nosys`). |
| 265 | [nosys](../../../xnu/bsd/kern/syscalls.master#L411) | `(!(SYSV_SHM))` | Unavailable/reserved implementation (`nosys`). |
| 266 | [shm_open](../../../xnu/bsd/kern/syscalls.master#L413) · [mechanism](local-ipc.md#266-shm_open) | `always` |  |
| 267 | [shm_unlink](../../../xnu/bsd/kern/syscalls.master#L414) · [mechanism](local-ipc.md#267-shm_unlink) | `always` |  |
| 268 | [sem_open](../../../xnu/bsd/kern/syscalls.master#L415) · [mechanism](local-ipc.md#268-sem_open) | `always` |  |
| 269 | [sem_close](../../../xnu/bsd/kern/syscalls.master#L416) · [mechanism](local-ipc.md#269-sem_close) | `always` |  |
| 270 | [sem_unlink](../../../xnu/bsd/kern/syscalls.master#L417) · [mechanism](local-ipc.md#270-sem_unlink) | `always` |  |
| 271 | [sem_wait](../../../xnu/bsd/kern/syscalls.master#L418) · [mechanism](local-ipc.md#271-sem_wait) | `always` |  |
| 272 | [sem_trywait](../../../xnu/bsd/kern/syscalls.master#L419) · [mechanism](local-ipc.md#272-sem_trywait) | `always` |  |
| 273 | [sem_post](../../../xnu/bsd/kern/syscalls.master#L420) · [mechanism](local-ipc.md#273-sem_post) | `always` |  |
| 274 | [sys_sysctlbyname](../../../xnu/bsd/kern/syscalls.master#L421) · [mechanism](diagnostics-and-system-control.md#274-sys_sysctlbyname) | `always` |  |
| 275 | [enosys](../../../xnu/bsd/kern/syscalls.master#L422) | `always` | old sem_init |
| 276 | [enosys](../../../xnu/bsd/kern/syscalls.master#L423) | `always` | old sem_destroy |
| 277 | [open_extended](../../../xnu/bsd/kern/syscalls.master#L424) · [mechanism](files-and-descriptors.md#277-open_extended) | `always` |  |
| 278 | [umask_extended](../../../xnu/bsd/kern/syscalls.master#L425) · [mechanism](filesystem-metadata.md#278-umask_extended) | `always` |  |
| 279 | [stat_extended](../../../xnu/bsd/kern/syscalls.master#L426) · [mechanism](filesystem-metadata.md#279-stat_extended) | `always` |  |
| 280 | [lstat_extended](../../../xnu/bsd/kern/syscalls.master#L427) · [mechanism](filesystem-metadata.md#280-lstat_extended) | `always` |  |
| 281 | [sys_fstat_extended](../../../xnu/bsd/kern/syscalls.master#L428) · [mechanism](filesystem-metadata.md#281-sys_fstat_extended) | `always` |  |
| 282 | [chmod_extended](../../../xnu/bsd/kern/syscalls.master#L429) · [mechanism](filesystem-metadata.md#282-chmod_extended) | `always` |  |
| 283 | [fchmod_extended](../../../xnu/bsd/kern/syscalls.master#L430) · [mechanism](filesystem-metadata.md#283-fchmod_extended) | `always` |  |
| 284 | [access_extended](../../../xnu/bsd/kern/syscalls.master#L431) · [mechanism](filesystem-metadata.md#284-access_extended) | `always` |  |
| 285 | [sys_settid](../../../xnu/bsd/kern/syscalls.master#L432) · [mechanism](processes-credentials-and-policy.md#285-sys_settid) | `always` |  |
| 286 | [gettid](../../../xnu/bsd/kern/syscalls.master#L433) · [mechanism](processes-credentials-and-policy.md#286-gettid) | `always` |  |
| 287 | [setsgroups](../../../xnu/bsd/kern/syscalls.master#L434) · [mechanism](processes-credentials-and-policy.md#287-setsgroups) | `always` |  |
| 288 | [getsgroups](../../../xnu/bsd/kern/syscalls.master#L435) · [mechanism](processes-credentials-and-policy.md#288-getsgroups) | `always` |  |
| 289 | [setwgroups](../../../xnu/bsd/kern/syscalls.master#L436) · [mechanism](processes-credentials-and-policy.md#289-setwgroups) | `always` |  |
| 290 | [getwgroups](../../../xnu/bsd/kern/syscalls.master#L437) · [mechanism](processes-credentials-and-policy.md#290-getwgroups) | `always` |  |
| 291 | [mkfifo_extended](../../../xnu/bsd/kern/syscalls.master#L438) · [mechanism](filesystem-namespace.md#291-mkfifo_extended) | `always` |  |
| 292 | [mkdir_extended](../../../xnu/bsd/kern/syscalls.master#L439) · [mechanism](filesystem-namespace.md#292-mkdir_extended) | `always` |  |
| 293 | [identitysvc](../../../xnu/bsd/kern/syscalls.master#L441) · [mechanism](processes-credentials-and-policy.md#293-identitysvc) | `(CONFIG_EXT_RESOLVER)` |  |
| 293 | [nosys](../../../xnu/bsd/kern/syscalls.master#L443) | `(!(CONFIG_EXT_RESOLVER))` | Unavailable/reserved implementation (`nosys`). |
| 294 | [shared_region_check_np](../../../xnu/bsd/kern/syscalls.master#L445) · [mechanism](virtual-memory.md#294-shared_region_check_np) | `always` |  |
| 295 | [nosys](../../../xnu/bsd/kern/syscalls.master#L446) | `always` | old shared_region_map_np |
| 296 | [vm_pressure_monitor](../../../xnu/bsd/kern/syscalls.master#L447) · [mechanism](virtual-memory.md#296-vm_pressure_monitor) | `always` |  |
| 297 | [psynch_rw_longrdlock](../../../xnu/bsd/kern/syscalls.master#L449) · [mechanism](events-pthreads-and-async-io.md#297-psynch_rw_longrdlock) | `(PSYNCH)` |  |
| 298 | [psynch_rw_yieldwrlock](../../../xnu/bsd/kern/syscalls.master#L450) · [mechanism](events-pthreads-and-async-io.md#298-psynch_rw_yieldwrlock) | `(PSYNCH)` |  |
| 299 | [psynch_rw_downgrade](../../../xnu/bsd/kern/syscalls.master#L451) · [mechanism](events-pthreads-and-async-io.md#299-psynch_rw_downgrade) | `(PSYNCH)` |  |
| 300 | [psynch_rw_upgrade](../../../xnu/bsd/kern/syscalls.master#L452) · [mechanism](events-pthreads-and-async-io.md#300-psynch_rw_upgrade) | `(PSYNCH)` |  |
| 301 | [psynch_mutexwait](../../../xnu/bsd/kern/syscalls.master#L453) · [mechanism](events-pthreads-and-async-io.md#301-psynch_mutexwait) | `(PSYNCH)` |  |
| 302 | [psynch_mutexdrop](../../../xnu/bsd/kern/syscalls.master#L454) · [mechanism](events-pthreads-and-async-io.md#302-psynch_mutexdrop) | `(PSYNCH)` |  |
| 303 | [psynch_cvbroad](../../../xnu/bsd/kern/syscalls.master#L455) · [mechanism](events-pthreads-and-async-io.md#303-psynch_cvbroad) | `(PSYNCH)` |  |
| 304 | [psynch_cvsignal](../../../xnu/bsd/kern/syscalls.master#L456) · [mechanism](events-pthreads-and-async-io.md#304-psynch_cvsignal) | `(PSYNCH)` |  |
| 305 | [psynch_cvwait](../../../xnu/bsd/kern/syscalls.master#L457) · [mechanism](events-pthreads-and-async-io.md#305-psynch_cvwait) | `(PSYNCH)` |  |
| 306 | [psynch_rw_rdlock](../../../xnu/bsd/kern/syscalls.master#L458) · [mechanism](events-pthreads-and-async-io.md#306-psynch_rw_rdlock) | `(PSYNCH)` |  |
| 307 | [psynch_rw_wrlock](../../../xnu/bsd/kern/syscalls.master#L459) · [mechanism](events-pthreads-and-async-io.md#307-psynch_rw_wrlock) | `(PSYNCH)` |  |
| 308 | [psynch_rw_unlock](../../../xnu/bsd/kern/syscalls.master#L460) · [mechanism](events-pthreads-and-async-io.md#308-psynch_rw_unlock) | `(PSYNCH)` |  |
| 309 | [psynch_rw_unlock2](../../../xnu/bsd/kern/syscalls.master#L461) · [mechanism](events-pthreads-and-async-io.md#309-psynch_rw_unlock2) | `(PSYNCH)` |  |
| 297 | [nosys](../../../xnu/bsd/kern/syscalls.master#L463) | `(!(PSYNCH))` | old reset_shared_file |
| 298 | [nosys](../../../xnu/bsd/kern/syscalls.master#L464) | `(!(PSYNCH))` | old new_system_shared_regions |
| 299 | [enosys](../../../xnu/bsd/kern/syscalls.master#L465) | `(!(PSYNCH))` | old shared_region_map_file_np |
| 300 | [enosys](../../../xnu/bsd/kern/syscalls.master#L466) | `(!(PSYNCH))` | old shared_region_make_private_np |
| 301 | [nosys](../../../xnu/bsd/kern/syscalls.master#L467) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 302 | [nosys](../../../xnu/bsd/kern/syscalls.master#L468) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 303 | [nosys](../../../xnu/bsd/kern/syscalls.master#L469) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 304 | [nosys](../../../xnu/bsd/kern/syscalls.master#L470) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 305 | [nosys](../../../xnu/bsd/kern/syscalls.master#L471) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 306 | [nosys](../../../xnu/bsd/kern/syscalls.master#L472) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 307 | [nosys](../../../xnu/bsd/kern/syscalls.master#L473) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 308 | [nosys](../../../xnu/bsd/kern/syscalls.master#L474) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 309 | [nosys](../../../xnu/bsd/kern/syscalls.master#L475) | `(!(PSYNCH))` | Unavailable/reserved implementation (`nosys`). |
| 310 | [getsid](../../../xnu/bsd/kern/syscalls.master#L477) · [mechanism](processes-credentials-and-policy.md#310-getsid) | `always` |  |
| 311 | [sys_settid_with_pid](../../../xnu/bsd/kern/syscalls.master#L478) · [mechanism](processes-credentials-and-policy.md#311-sys_settid_with_pid) | `always` |  |
| 312 | [psynch_cvclrprepost](../../../xnu/bsd/kern/syscalls.master#L480) · [mechanism](events-pthreads-and-async-io.md#312-psynch_cvclrprepost) | `(PSYNCH)` |  |
| 312 | [nosys](../../../xnu/bsd/kern/syscalls.master#L482) | `(!(PSYNCH))` | old __pthread_cond_timedwait |
| 313 | [aio_fsync](../../../xnu/bsd/kern/syscalls.master#L484) · [mechanism](events-pthreads-and-async-io.md#313-aio_fsync) | `always` |  |
| 314 | [aio_return](../../../xnu/bsd/kern/syscalls.master#L485) · [mechanism](events-pthreads-and-async-io.md#314-aio_return) | `always` |  |
| 315 | [aio_suspend](../../../xnu/bsd/kern/syscalls.master#L486) · [mechanism](events-pthreads-and-async-io.md#315-aio_suspend) | `always` |  |
| 316 | [aio_cancel](../../../xnu/bsd/kern/syscalls.master#L487) · [mechanism](events-pthreads-and-async-io.md#316-aio_cancel) | `always` |  |
| 317 | [aio_error](../../../xnu/bsd/kern/syscalls.master#L488) · [mechanism](events-pthreads-and-async-io.md#317-aio_error) | `always` |  |
| 318 | [aio_read](../../../xnu/bsd/kern/syscalls.master#L489) · [mechanism](events-pthreads-and-async-io.md#318-aio_read) | `always` |  |
| 319 | [aio_write](../../../xnu/bsd/kern/syscalls.master#L490) · [mechanism](events-pthreads-and-async-io.md#319-aio_write) | `always` |  |
| 320 | [lio_listio](../../../xnu/bsd/kern/syscalls.master#L491) · [mechanism](events-pthreads-and-async-io.md#320-lio_listio) | `always` |  |
| 321 | [nosys](../../../xnu/bsd/kern/syscalls.master#L492) | `always` | old __pthread_cond_wait |
| 322 | [iopolicysys](../../../xnu/bsd/kern/syscalls.master#L493) · [mechanism](processes-credentials-and-policy.md#322-iopolicysys) | `always` |  |
| 323 | [process_policy](../../../xnu/bsd/kern/syscalls.master#L494) · [mechanism](processes-credentials-and-policy.md#323-process_policy) | `always` |  |
| 324 | [mlockall](../../../xnu/bsd/kern/syscalls.master#L495) · [mechanism](virtual-memory.md#324-mlockall) | `always` |  |
| 325 | [munlockall](../../../xnu/bsd/kern/syscalls.master#L496) · [mechanism](virtual-memory.md#325-munlockall) | `always` |  |
| 326 | [nosys](../../../xnu/bsd/kern/syscalls.master#L497) | `always` | Unavailable/reserved implementation (`nosys`). |
| 327 | [issetugid](../../../xnu/bsd/kern/syscalls.master#L498) · [mechanism](processes-credentials-and-policy.md#327-issetugid) | `always` |  |
| 328 | [__pthread_kill](../../../xnu/bsd/kern/syscalls.master#L499) · [mechanism](signals-and-thread-control.md#328-__pthread_kill) | `always` |  |
| 329 | [__pthread_sigmask](../../../xnu/bsd/kern/syscalls.master#L500) · [mechanism](signals-and-thread-control.md#329-__pthread_sigmask) | `always` |  |
| 330 | [__sigwait](../../../xnu/bsd/kern/syscalls.master#L501) · [mechanism](signals-and-thread-control.md#330-__sigwait) | `always` |  |
| 331 | [__disable_threadsignal](../../../xnu/bsd/kern/syscalls.master#L502) · [mechanism](signals-and-thread-control.md#331-__disable_threadsignal) | `always` |  |
| 332 | [__pthread_markcancel](../../../xnu/bsd/kern/syscalls.master#L503) · [mechanism](signals-and-thread-control.md#332-__pthread_markcancel) | `always` |  |
| 333 | [__pthread_canceled](../../../xnu/bsd/kern/syscalls.master#L504) · [mechanism](signals-and-thread-control.md#333-__pthread_canceled) | `always` |  |
| 334 | [__semwait_signal](../../../xnu/bsd/kern/syscalls.master#L509) · [mechanism](signals-and-thread-control.md#334-__semwait_signal) | `always` |  |
| 335 | [nosys](../../../xnu/bsd/kern/syscalls.master#L512) | `always` | old utrace |
| 336 | [proc_info](../../../xnu/bsd/kern/syscalls.master#L513) · [mechanism](processes-credentials-and-policy.md#336-proc_info) | `always` |  |
| 337 | [sendfile](../../../xnu/bsd/kern/syscalls.master#L515) · [mechanism](sockets-and-network-policy.md#337-sendfile) | `(SENDFILE)` |  |
| 337 | [nosys](../../../xnu/bsd/kern/syscalls.master#L517) | `(!(SENDFILE))` | Unavailable/reserved implementation (`nosys`). |
| 338 | [stat64](../../../xnu/bsd/kern/syscalls.master#L519) · [mechanism](filesystem-metadata.md#338-stat64) | `always` |  |
| 339 | [sys_fstat64](../../../xnu/bsd/kern/syscalls.master#L520) · [mechanism](filesystem-metadata.md#339-sys_fstat64) | `always` |  |
| 340 | [lstat64](../../../xnu/bsd/kern/syscalls.master#L521) · [mechanism](filesystem-metadata.md#340-lstat64) | `always` |  |
| 341 | [stat64_extended](../../../xnu/bsd/kern/syscalls.master#L522) · [mechanism](filesystem-metadata.md#341-stat64_extended) | `always` |  |
| 342 | [lstat64_extended](../../../xnu/bsd/kern/syscalls.master#L523) · [mechanism](filesystem-metadata.md#342-lstat64_extended) | `always` |  |
| 343 | [sys_fstat64_extended](../../../xnu/bsd/kern/syscalls.master#L524) · [mechanism](filesystem-metadata.md#343-sys_fstat64_extended) | `always` |  |
| 344 | [getdirentries64](../../../xnu/bsd/kern/syscalls.master#L525) · [mechanism](filesystem-metadata.md#344-getdirentries64) | `always` |  |
| 345 | [statfs64](../../../xnu/bsd/kern/syscalls.master#L526) · [mechanism](filesystem-mounts-and-control.md#345-statfs64) | `always` |  |
| 346 | [fstatfs64](../../../xnu/bsd/kern/syscalls.master#L527) · [mechanism](filesystem-mounts-and-control.md#346-fstatfs64) | `always` |  |
| 347 | [getfsstat64](../../../xnu/bsd/kern/syscalls.master#L528) · [mechanism](filesystem-mounts-and-control.md#347-getfsstat64) | `always` |  |
| 348 | [__pthread_chdir](../../../xnu/bsd/kern/syscalls.master#L529) · [mechanism](filesystem-namespace.md#348-__pthread_chdir) | `always` |  |
| 349 | [__pthread_fchdir](../../../xnu/bsd/kern/syscalls.master#L530) · [mechanism](filesystem-namespace.md#349-__pthread_fchdir) | `always` |  |
| 350 | [audit](../../../xnu/bsd/kern/syscalls.master#L531) · [mechanism](security-and-audit.md#350-audit) | `always` |  |
| 351 | [auditon](../../../xnu/bsd/kern/syscalls.master#L532) · [mechanism](security-and-audit.md#351-auditon) | `always` |  |
| 352 | [nosys](../../../xnu/bsd/kern/syscalls.master#L533) | `always` | Unavailable/reserved implementation (`nosys`). |
| 353 | [getauid](../../../xnu/bsd/kern/syscalls.master#L534) · [mechanism](security-and-audit.md#353-getauid) | `always` |  |
| 354 | [setauid](../../../xnu/bsd/kern/syscalls.master#L535) · [mechanism](security-and-audit.md#354-setauid) | `always` |  |
| 355 | [nosys](../../../xnu/bsd/kern/syscalls.master#L536) | `always` | old getaudit |
| 356 | [nosys](../../../xnu/bsd/kern/syscalls.master#L537) | `always` | old setaudit |
| 357 | [getaudit_addr](../../../xnu/bsd/kern/syscalls.master#L538) · [mechanism](security-and-audit.md#357-getaudit_addr) | `always` |  |
| 358 | [setaudit_addr](../../../xnu/bsd/kern/syscalls.master#L539) · [mechanism](security-and-audit.md#358-setaudit_addr) | `always` |  |
| 359 | [auditctl](../../../xnu/bsd/kern/syscalls.master#L540) · [mechanism](security-and-audit.md#359-auditctl) | `always` |  |
| 360 | [bsdthread_create](../../../xnu/bsd/kern/syscalls.master#L541) · [mechanism](events-pthreads-and-async-io.md#360-bsdthread_create) | `always` |  |
| 361 | [bsdthread_terminate](../../../xnu/bsd/kern/syscalls.master#L542) · [mechanism](events-pthreads-and-async-io.md#361-bsdthread_terminate) | `always` |  |
| 362 | [kqueue](../../../xnu/bsd/kern/syscalls.master#L543) · [mechanism](events-pthreads-and-async-io.md#362-kqueue) | `always` |  |
| 363 | [kevent](../../../xnu/bsd/kern/syscalls.master#L544) · [mechanism](events-pthreads-and-async-io.md#363-kevent) | `always` |  |
| 364 | [lchown](../../../xnu/bsd/kern/syscalls.master#L545) · [mechanism](filesystem-metadata.md#364-lchown) | `always` |  |
| 365 | [nosys](../../../xnu/bsd/kern/syscalls.master#L546) | `always` | old stack_snapshot |
| 366 | [bsdthread_register](../../../xnu/bsd/kern/syscalls.master#L547) · [mechanism](events-pthreads-and-async-io.md#366-bsdthread_register) | `always` |  |
| 367 | [workq_open](../../../xnu/bsd/kern/syscalls.master#L548) · [mechanism](events-pthreads-and-async-io.md#367-workq_open) | `always` |  |
| 368 | [workq_kernreturn](../../../xnu/bsd/kern/syscalls.master#L549) · [mechanism](events-pthreads-and-async-io.md#368-workq_kernreturn) | `always` |  |
| 369 | [kevent64](../../../xnu/bsd/kern/syscalls.master#L550) · [mechanism](events-pthreads-and-async-io.md#369-kevent64) | `always` |  |
| 370 | [nosys](../../../xnu/bsd/kern/syscalls.master#L551) | `always` | old __semwait_signal |
| 371 | [nosys](../../../xnu/bsd/kern/syscalls.master#L552) | `always` | old __semwait_signal |
| 372 | [thread_selfid](../../../xnu/bsd/kern/syscalls.master#L553) · [mechanism](events-pthreads-and-async-io.md#372-thread_selfid) | `always` |  |
| 373 | [ledger](../../../xnu/bsd/kern/syscalls.master#L554) · [mechanism](time-and-accounting.md#373-ledger) | `always` |  |
| 374 | [kevent_qos](../../../xnu/bsd/kern/syscalls.master#L555) · [mechanism](events-pthreads-and-async-io.md#374-kevent_qos) | `always` |  |
| 375 | [kevent_id](../../../xnu/bsd/kern/syscalls.master#L556) · [mechanism](events-pthreads-and-async-io.md#375-kevent_id) | `always` |  |
| 376 | [nosys](../../../xnu/bsd/kern/syscalls.master#L557) | `always` | Unavailable/reserved implementation (`nosys`). |
| 377 | [nosys](../../../xnu/bsd/kern/syscalls.master#L558) | `always` | Unavailable/reserved implementation (`nosys`). |
| 378 | [nosys](../../../xnu/bsd/kern/syscalls.master#L559) | `always` | Unavailable/reserved implementation (`nosys`). |
| 379 | [nosys](../../../xnu/bsd/kern/syscalls.master#L560) | `always` | Unavailable/reserved implementation (`nosys`). |
| 380 | [__mac_execve](../../../xnu/bsd/kern/syscalls.master#L561) · [mechanism](processes-credentials-and-policy.md#380-__mac_execve) | `always` |  |
| 381 | [__mac_syscall](../../../xnu/bsd/kern/syscalls.master#L563) · [mechanism](security-and-audit.md#381-__mac_syscall) | `(CONFIG_MACF)` |  |
| 382 | [__mac_get_file](../../../xnu/bsd/kern/syscalls.master#L564) · [mechanism](security-and-audit.md#382-__mac_get_file) | `(CONFIG_MACF)` |  |
| 383 | [__mac_set_file](../../../xnu/bsd/kern/syscalls.master#L565) · [mechanism](security-and-audit.md#383-__mac_set_file) | `(CONFIG_MACF)` |  |
| 384 | [__mac_get_link](../../../xnu/bsd/kern/syscalls.master#L566) · [mechanism](security-and-audit.md#384-__mac_get_link) | `(CONFIG_MACF)` |  |
| 385 | [__mac_set_link](../../../xnu/bsd/kern/syscalls.master#L567) · [mechanism](security-and-audit.md#385-__mac_set_link) | `(CONFIG_MACF)` |  |
| 386 | [__mac_get_proc](../../../xnu/bsd/kern/syscalls.master#L568) · [mechanism](security-and-audit.md#386-__mac_get_proc) | `(CONFIG_MACF)` |  |
| 387 | [__mac_set_proc](../../../xnu/bsd/kern/syscalls.master#L569) · [mechanism](security-and-audit.md#387-__mac_set_proc) | `(CONFIG_MACF)` |  |
| 388 | [__mac_get_fd](../../../xnu/bsd/kern/syscalls.master#L570) · [mechanism](security-and-audit.md#388-__mac_get_fd) | `(CONFIG_MACF)` |  |
| 389 | [__mac_set_fd](../../../xnu/bsd/kern/syscalls.master#L571) · [mechanism](security-and-audit.md#389-__mac_set_fd) | `(CONFIG_MACF)` |  |
| 390 | [__mac_get_pid](../../../xnu/bsd/kern/syscalls.master#L572) · [mechanism](security-and-audit.md#390-__mac_get_pid) | `(CONFIG_MACF)` |  |
| 381 | [enosys](../../../xnu/bsd/kern/syscalls.master#L574) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`enosys`). |
| 382 | [nosys](../../../xnu/bsd/kern/syscalls.master#L575) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 383 | [nosys](../../../xnu/bsd/kern/syscalls.master#L576) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 384 | [nosys](../../../xnu/bsd/kern/syscalls.master#L577) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 385 | [nosys](../../../xnu/bsd/kern/syscalls.master#L578) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 386 | [nosys](../../../xnu/bsd/kern/syscalls.master#L579) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 387 | [nosys](../../../xnu/bsd/kern/syscalls.master#L580) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 388 | [nosys](../../../xnu/bsd/kern/syscalls.master#L581) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 389 | [nosys](../../../xnu/bsd/kern/syscalls.master#L582) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 390 | [nosys](../../../xnu/bsd/kern/syscalls.master#L583) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 391 | [enosys](../../../xnu/bsd/kern/syscalls.master#L585) | `always` | Unavailable/reserved implementation (`enosys`). |
| 392 | [enosys](../../../xnu/bsd/kern/syscalls.master#L586) | `always` | Unavailable/reserved implementation (`enosys`). |
| 393 | [enosys](../../../xnu/bsd/kern/syscalls.master#L587) | `always` | Unavailable/reserved implementation (`enosys`). |
| 394 | [pselect](../../../xnu/bsd/kern/syscalls.master#L588) · [mechanism](events-pthreads-and-async-io.md#394-pselect) | `always` |  |
| 395 | [pselect_nocancel](../../../xnu/bsd/kern/syscalls.master#L589) · [mechanism](events-pthreads-and-async-io.md#395-pselect_nocancel) | `always` |  |
| 396 | [read_nocancel](../../../xnu/bsd/kern/syscalls.master#L590) · [mechanism](files-and-descriptors.md#396-read_nocancel) | `always` |  |
| 397 | [write_nocancel](../../../xnu/bsd/kern/syscalls.master#L591) · [mechanism](files-and-descriptors.md#397-write_nocancel) | `always` |  |
| 398 | [open_nocancel](../../../xnu/bsd/kern/syscalls.master#L592) · [mechanism](files-and-descriptors.md#398-open_nocancel) | `always` |  |
| 399 | [sys_close_nocancel](../../../xnu/bsd/kern/syscalls.master#L593) · [mechanism](files-and-descriptors.md#399-sys_close_nocancel) | `always` |  |
| 400 | [wait4_nocancel](../../../xnu/bsd/kern/syscalls.master#L594) · [mechanism](processes-credentials-and-policy.md#400-wait4_nocancel) | `always` |  |
| 401 | [recvmsg_nocancel](../../../xnu/bsd/kern/syscalls.master#L596) · [mechanism](sockets-and-network-policy.md#401-recvmsg_nocancel) | `(SOCKETS)` |  |
| 402 | [sendmsg_nocancel](../../../xnu/bsd/kern/syscalls.master#L597) · [mechanism](sockets-and-network-policy.md#402-sendmsg_nocancel) | `(SOCKETS)` |  |
| 403 | [recvfrom_nocancel](../../../xnu/bsd/kern/syscalls.master#L598) · [mechanism](sockets-and-network-policy.md#403-recvfrom_nocancel) | `(SOCKETS)` |  |
| 404 | [accept_nocancel](../../../xnu/bsd/kern/syscalls.master#L599) · [mechanism](sockets-and-network-policy.md#404-accept_nocancel) | `(SOCKETS)` |  |
| 401 | [nosys](../../../xnu/bsd/kern/syscalls.master#L601) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 402 | [nosys](../../../xnu/bsd/kern/syscalls.master#L602) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 403 | [nosys](../../../xnu/bsd/kern/syscalls.master#L603) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 404 | [nosys](../../../xnu/bsd/kern/syscalls.master#L604) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 405 | [msync_nocancel](../../../xnu/bsd/kern/syscalls.master#L606) · [mechanism](virtual-memory.md#405-msync_nocancel) | `always` |  |
| 406 | [sys_fcntl_nocancel](../../../xnu/bsd/kern/syscalls.master#L607) · [mechanism](files-and-descriptors.md#406-sys_fcntl_nocancel) | `always` |  |
| 407 | [select_nocancel](../../../xnu/bsd/kern/syscalls.master#L608) · [mechanism](events-pthreads-and-async-io.md#407-select_nocancel) | `always` |  |
| 408 | [fsync_nocancel](../../../xnu/bsd/kern/syscalls.master#L609) · [mechanism](filesystem-mounts-and-control.md#408-fsync_nocancel) | `always` |  |
| 409 | [connect_nocancel](../../../xnu/bsd/kern/syscalls.master#L611) · [mechanism](sockets-and-network-policy.md#409-connect_nocancel) | `(SOCKETS)` |  |
| 409 | [nosys](../../../xnu/bsd/kern/syscalls.master#L613) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 410 | [sigsuspend_nocancel](../../../xnu/bsd/kern/syscalls.master#L615) · [mechanism](signals-and-thread-control.md#410-sigsuspend_nocancel) | `always` |  |
| 411 | [readv_nocancel](../../../xnu/bsd/kern/syscalls.master#L616) · [mechanism](files-and-descriptors.md#411-readv_nocancel) | `always` |  |
| 412 | [writev_nocancel](../../../xnu/bsd/kern/syscalls.master#L617) · [mechanism](files-and-descriptors.md#412-writev_nocancel) | `always` |  |
| 413 | [sendto_nocancel](../../../xnu/bsd/kern/syscalls.master#L619) · [mechanism](sockets-and-network-policy.md#413-sendto_nocancel) | `(SOCKETS)` |  |
| 413 | [nosys](../../../xnu/bsd/kern/syscalls.master#L621) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 414 | [pread_nocancel](../../../xnu/bsd/kern/syscalls.master#L623) · [mechanism](files-and-descriptors.md#414-pread_nocancel) | `always` |  |
| 415 | [pwrite_nocancel](../../../xnu/bsd/kern/syscalls.master#L624) · [mechanism](files-and-descriptors.md#415-pwrite_nocancel) | `always` |  |
| 416 | [waitid_nocancel](../../../xnu/bsd/kern/syscalls.master#L625) · [mechanism](processes-credentials-and-policy.md#416-waitid_nocancel) | `always` |  |
| 417 | [poll_nocancel](../../../xnu/bsd/kern/syscalls.master#L626) · [mechanism](events-pthreads-and-async-io.md#417-poll_nocancel) | `always` |  |
| 418 | [msgsnd_nocancel](../../../xnu/bsd/kern/syscalls.master#L628) · [mechanism](local-ipc.md#418-msgsnd_nocancel) | `(SYSV_MSG)` |  |
| 419 | [msgrcv_nocancel](../../../xnu/bsd/kern/syscalls.master#L629) · [mechanism](local-ipc.md#419-msgrcv_nocancel) | `(SYSV_MSG)` |  |
| 418 | [nosys](../../../xnu/bsd/kern/syscalls.master#L631) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 419 | [nosys](../../../xnu/bsd/kern/syscalls.master#L632) | `(!(SYSV_MSG))` | Unavailable/reserved implementation (`nosys`). |
| 420 | [sem_wait_nocancel](../../../xnu/bsd/kern/syscalls.master#L634) · [mechanism](local-ipc.md#420-sem_wait_nocancel) | `always` |  |
| 421 | [aio_suspend_nocancel](../../../xnu/bsd/kern/syscalls.master#L635) · [mechanism](events-pthreads-and-async-io.md#421-aio_suspend_nocancel) | `always` |  |
| 422 | [__sigwait_nocancel](../../../xnu/bsd/kern/syscalls.master#L636) · [mechanism](signals-and-thread-control.md#422-__sigwait_nocancel) | `always` |  |
| 423 | [__semwait_signal_nocancel](../../../xnu/bsd/kern/syscalls.master#L637) · [mechanism](signals-and-thread-control.md#423-__semwait_signal_nocancel) | `always` |  |
| 424 | [__mac_mount](../../../xnu/bsd/kern/syscalls.master#L638) · [mechanism](filesystem-mounts-and-control.md#424-__mac_mount) | `always` |  |
| 425 | [__mac_get_mount](../../../xnu/bsd/kern/syscalls.master#L640) · [mechanism](filesystem-mounts-and-control.md#425-__mac_get_mount) | `(CONFIG_MACF)` |  |
| 425 | [nosys](../../../xnu/bsd/kern/syscalls.master#L642) | `(!(CONFIG_MACF))` | Unavailable/reserved implementation (`nosys`). |
| 426 | [__mac_getfsstat](../../../xnu/bsd/kern/syscalls.master#L644) · [mechanism](filesystem-mounts-and-control.md#426-__mac_getfsstat) | `always` |  |
| 427 | [fsgetpath](../../../xnu/bsd/kern/syscalls.master#L645) · [mechanism](filesystem-metadata.md#427-fsgetpath) | `always` | private fsgetpath (File Manager SPI) |
| 428 | [audit_session_self](../../../xnu/bsd/kern/syscalls.master#L646) · [mechanism](security-and-audit.md#428-audit_session_self) | `always` |  |
| 429 | [audit_session_join](../../../xnu/bsd/kern/syscalls.master#L647) · [mechanism](security-and-audit.md#429-audit_session_join) | `always` |  |
| 430 | [sys_fileport_makeport](../../../xnu/bsd/kern/syscalls.master#L648) · [mechanism](files-and-descriptors.md#430-sys_fileport_makeport) | `always` |  |
| 431 | [sys_fileport_makefd](../../../xnu/bsd/kern/syscalls.master#L649) · [mechanism](files-and-descriptors.md#431-sys_fileport_makefd) | `always` |  |
| 432 | [audit_session_port](../../../xnu/bsd/kern/syscalls.master#L650) · [mechanism](security-and-audit.md#432-audit_session_port) | `always` |  |
| 433 | [pid_suspend](../../../xnu/bsd/kern/syscalls.master#L651) · [mechanism](processes-credentials-and-policy.md#433-pid_suspend) | `always` |  |
| 434 | [pid_resume](../../../xnu/bsd/kern/syscalls.master#L652) · [mechanism](processes-credentials-and-policy.md#434-pid_resume) | `always` |  |
| 435 | [pid_hibernate](../../../xnu/bsd/kern/syscalls.master#L654) · [mechanism](processes-credentials-and-policy.md#435-pid_hibernate) | `(CONFIG_EMBEDDED)` |  |
| 435 | [nosys](../../../xnu/bsd/kern/syscalls.master#L656) | `(!(CONFIG_EMBEDDED))` | Unavailable/reserved implementation (`nosys`). |
| 436 | [pid_shutdown_sockets](../../../xnu/bsd/kern/syscalls.master#L659) · [mechanism](processes-credentials-and-policy.md#436-pid_shutdown_sockets) | `(SOCKETS)` |  |
| 436 | [nosys](../../../xnu/bsd/kern/syscalls.master#L661) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 437 | [nosys](../../../xnu/bsd/kern/syscalls.master#L663) | `always` | old shared_region_slide_np |
| 438 | [nosys](../../../xnu/bsd/kern/syscalls.master#L664) | `always` | old shared_region_map_and_slide_np |
| 439 | [kas_info](../../../xnu/bsd/kern/syscalls.master#L665) · [mechanism](virtual-memory.md#439-kas_info) | `always` |  |
| 440 | [memorystatus_control](../../../xnu/bsd/kern/syscalls.master#L667) · [mechanism](virtual-memory.md#440-memorystatus_control) | `(CONFIG_MEMORYSTATUS)` |  |
| 440 | [nosys](../../../xnu/bsd/kern/syscalls.master#L669) | `(!(CONFIG_MEMORYSTATUS))` | Unavailable/reserved implementation (`nosys`). |
| 441 | [guarded_open_np](../../../xnu/bsd/kern/syscalls.master#L671) · [mechanism](files-and-descriptors.md#441-guarded_open_np) | `always` |  |
| 442 | [guarded_close_np](../../../xnu/bsd/kern/syscalls.master#L672) · [mechanism](files-and-descriptors.md#442-guarded_close_np) | `always` |  |
| 443 | [guarded_kqueue_np](../../../xnu/bsd/kern/syscalls.master#L673) · [mechanism](events-pthreads-and-async-io.md#443-guarded_kqueue_np) | `always` |  |
| 444 | [change_fdguard_np](../../../xnu/bsd/kern/syscalls.master#L674) · [mechanism](files-and-descriptors.md#444-change_fdguard_np) | `always` |  |
| 445 | [usrctl](../../../xnu/bsd/kern/syscalls.master#L675) · [mechanism](processes-credentials-and-policy.md#445-usrctl) | `always` |  |
| 446 | [proc_rlimit_control](../../../xnu/bsd/kern/syscalls.master#L676) · [mechanism](processes-credentials-and-policy.md#446-proc_rlimit_control) | `always` |  |
| 447 | [connectx](../../../xnu/bsd/kern/syscalls.master#L678) · [mechanism](sockets-and-network-policy.md#447-connectx) | `(SOCKETS)` |  |
| 448 | [disconnectx](../../../xnu/bsd/kern/syscalls.master#L679) · [mechanism](sockets-and-network-policy.md#448-disconnectx) | `(SOCKETS)` |  |
| 449 | [peeloff](../../../xnu/bsd/kern/syscalls.master#L680) · [mechanism](sockets-and-network-policy.md#449-peeloff) | `(SOCKETS)` |  |
| 450 | [socket_delegate](../../../xnu/bsd/kern/syscalls.master#L681) · [mechanism](sockets-and-network-policy.md#450-socket_delegate) | `(SOCKETS)` |  |
| 447 | [nosys](../../../xnu/bsd/kern/syscalls.master#L683) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 448 | [nosys](../../../xnu/bsd/kern/syscalls.master#L684) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 449 | [nosys](../../../xnu/bsd/kern/syscalls.master#L685) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 450 | [nosys](../../../xnu/bsd/kern/syscalls.master#L686) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 451 | [telemetry](../../../xnu/bsd/kern/syscalls.master#L688) · [mechanism](diagnostics-and-system-control.md#451-telemetry) | `always` |  |
| 452 | [proc_uuid_policy](../../../xnu/bsd/kern/syscalls.master#L690) · [mechanism](processes-credentials-and-policy.md#452-proc_uuid_policy) | `(CONFIG_PROC_UUID_POLICY)` |  |
| 452 | [nosys](../../../xnu/bsd/kern/syscalls.master#L692) | `(!(CONFIG_PROC_UUID_POLICY))` | Unavailable/reserved implementation (`nosys`). |
| 453 | [memorystatus_get_level](../../../xnu/bsd/kern/syscalls.master#L695) · [mechanism](virtual-memory.md#453-memorystatus_get_level) | `(CONFIG_MEMORYSTATUS)` |  |
| 453 | [nosys](../../../xnu/bsd/kern/syscalls.master#L697) | `(!(CONFIG_MEMORYSTATUS))` | Unavailable/reserved implementation (`nosys`). |
| 454 | [system_override](../../../xnu/bsd/kern/syscalls.master#L699) · [mechanism](processes-credentials-and-policy.md#454-system_override) | `always` |  |
| 455 | [vfs_purge](../../../xnu/bsd/kern/syscalls.master#L700) · [mechanism](filesystem-mounts-and-control.md#455-vfs_purge) | `always` |  |
| 456 | [sfi_ctl](../../../xnu/bsd/kern/syscalls.master#L701) · [mechanism](processes-credentials-and-policy.md#456-sfi_ctl) | `always` |  |
| 457 | [sfi_pidctl](../../../xnu/bsd/kern/syscalls.master#L702) · [mechanism](processes-credentials-and-policy.md#457-sfi_pidctl) | `always` |  |
| 458 | [coalition](../../../xnu/bsd/kern/syscalls.master#L704) · [mechanism](processes-credentials-and-policy.md#458-coalition) | `(CONFIG_COALITIONS)` |  |
| 459 | [coalition_info](../../../xnu/bsd/kern/syscalls.master#L705) · [mechanism](processes-credentials-and-policy.md#459-coalition_info) | `(CONFIG_COALITIONS)` |  |
| 458 | [enosys](../../../xnu/bsd/kern/syscalls.master#L707) | `(!(CONFIG_COALITIONS))` | Unavailable/reserved implementation (`enosys`). |
| 459 | [enosys](../../../xnu/bsd/kern/syscalls.master#L708) | `(!(CONFIG_COALITIONS))` | Unavailable/reserved implementation (`enosys`). |
| 460 | [necp_match_policy](../../../xnu/bsd/kern/syscalls.master#L711) · [mechanism](sockets-and-network-policy.md#460-necp_match_policy) | `(NECP)` |  |
| 460 | [nosys](../../../xnu/bsd/kern/syscalls.master#L713) | `(!(NECP))` | Unavailable/reserved implementation (`nosys`). |
| 461 | [getattrlistbulk](../../../xnu/bsd/kern/syscalls.master#L715) · [mechanism](filesystem-metadata.md#461-getattrlistbulk) | `always` |  |
| 462 | [clonefileat](../../../xnu/bsd/kern/syscalls.master#L716) · [mechanism](filesystem-namespace.md#462-clonefileat) | `always` |  |
| 463 | [openat](../../../xnu/bsd/kern/syscalls.master#L717) · [mechanism](files-and-descriptors.md#463-openat) | `always` |  |
| 464 | [openat_nocancel](../../../xnu/bsd/kern/syscalls.master#L718) · [mechanism](files-and-descriptors.md#464-openat_nocancel) | `always` |  |
| 465 | [renameat](../../../xnu/bsd/kern/syscalls.master#L719) · [mechanism](filesystem-namespace.md#465-renameat) | `always` |  |
| 466 | [faccessat](../../../xnu/bsd/kern/syscalls.master#L720) · [mechanism](filesystem-metadata.md#466-faccessat) | `always` |  |
| 467 | [fchmodat](../../../xnu/bsd/kern/syscalls.master#L721) · [mechanism](filesystem-metadata.md#467-fchmodat) | `always` |  |
| 468 | [fchownat](../../../xnu/bsd/kern/syscalls.master#L722) · [mechanism](filesystem-metadata.md#468-fchownat) | `always` |  |
| 469 | [fstatat](../../../xnu/bsd/kern/syscalls.master#L723) · [mechanism](filesystem-metadata.md#469-fstatat) | `always` |  |
| 470 | [fstatat64](../../../xnu/bsd/kern/syscalls.master#L724) · [mechanism](filesystem-metadata.md#470-fstatat64) | `always` |  |
| 471 | [linkat](../../../xnu/bsd/kern/syscalls.master#L725) · [mechanism](filesystem-namespace.md#471-linkat) | `always` |  |
| 472 | [unlinkat](../../../xnu/bsd/kern/syscalls.master#L726) · [mechanism](filesystem-namespace.md#472-unlinkat) | `always` |  |
| 473 | [readlinkat](../../../xnu/bsd/kern/syscalls.master#L727) · [mechanism](filesystem-namespace.md#473-readlinkat) | `always` |  |
| 474 | [symlinkat](../../../xnu/bsd/kern/syscalls.master#L728) · [mechanism](filesystem-namespace.md#474-symlinkat) | `always` |  |
| 475 | [mkdirat](../../../xnu/bsd/kern/syscalls.master#L729) · [mechanism](filesystem-namespace.md#475-mkdirat) | `always` |  |
| 476 | [getattrlistat](../../../xnu/bsd/kern/syscalls.master#L730) · [mechanism](filesystem-metadata.md#476-getattrlistat) | `always` |  |
| 477 | [proc_trace_log](../../../xnu/bsd/kern/syscalls.master#L731) · [mechanism](diagnostics-and-system-control.md#477-proc_trace_log) | `always` |  |
| 478 | [bsdthread_ctl](../../../xnu/bsd/kern/syscalls.master#L732) · [mechanism](events-pthreads-and-async-io.md#478-bsdthread_ctl) | `always` |  |
| 479 | [openbyid_np](../../../xnu/bsd/kern/syscalls.master#L733) · [mechanism](files-and-descriptors.md#479-openbyid_np) | `always` |  |
| 480 | [recvmsg_x](../../../xnu/bsd/kern/syscalls.master#L735) · [mechanism](sockets-and-network-policy.md#480-recvmsg_x) | `(SOCKETS)` |  |
| 481 | [sendmsg_x](../../../xnu/bsd/kern/syscalls.master#L736) · [mechanism](sockets-and-network-policy.md#481-sendmsg_x) | `(SOCKETS)` |  |
| 480 | [nosys](../../../xnu/bsd/kern/syscalls.master#L738) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 481 | [nosys](../../../xnu/bsd/kern/syscalls.master#L739) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 482 | [thread_selfusage](../../../xnu/bsd/kern/syscalls.master#L741) · [mechanism](time-and-accounting.md#482-thread_selfusage) | `always` |  |
| 483 | [csrctl](../../../xnu/bsd/kern/syscalls.master#L743) · [mechanism](security-and-audit.md#483-csrctl) | `(CONFIG_CSR)` |  |
| 483 | [enosys](../../../xnu/bsd/kern/syscalls.master#L745) | `(!(CONFIG_CSR))` | Unavailable/reserved implementation (`enosys`). |
| 484 | [guarded_open_dprotected_np](../../../xnu/bsd/kern/syscalls.master#L747) · [mechanism](files-and-descriptors.md#484-guarded_open_dprotected_np) | `always` |  |
| 485 | [guarded_write_np](../../../xnu/bsd/kern/syscalls.master#L748) · [mechanism](files-and-descriptors.md#485-guarded_write_np) | `always` |  |
| 486 | [guarded_pwrite_np](../../../xnu/bsd/kern/syscalls.master#L749) · [mechanism](files-and-descriptors.md#486-guarded_pwrite_np) | `always` |  |
| 487 | [guarded_writev_np](../../../xnu/bsd/kern/syscalls.master#L750) · [mechanism](files-and-descriptors.md#487-guarded_writev_np) | `always` |  |
| 488 | [renameatx_np](../../../xnu/bsd/kern/syscalls.master#L751) · [mechanism](filesystem-namespace.md#488-renameatx_np) | `always` |  |
| 489 | [mremap_encrypted](../../../xnu/bsd/kern/syscalls.master#L753) · [mechanism](virtual-memory.md#489-mremap_encrypted) | `(CONFIG_CODE_DECRYPTION)` |  |
| 489 | [enosys](../../../xnu/bsd/kern/syscalls.master#L755) | `(!(CONFIG_CODE_DECRYPTION))` | Unavailable/reserved implementation (`enosys`). |
| 490 | [netagent_trigger](../../../xnu/bsd/kern/syscalls.master#L758) · [mechanism](sockets-and-network-policy.md#490-netagent_trigger) | `(NETWORKING)` |  |
| 490 | [nosys](../../../xnu/bsd/kern/syscalls.master#L760) | `(!(NETWORKING))` | Unavailable/reserved implementation (`nosys`). |
| 491 | [stack_snapshot_with_config](../../../xnu/bsd/kern/syscalls.master#L762) · [mechanism](diagnostics-and-system-control.md#491-stack_snapshot_with_config) | `always` |  |
| 492 | [microstackshot](../../../xnu/bsd/kern/syscalls.master#L764) · [mechanism](diagnostics-and-system-control.md#492-microstackshot) | `(CONFIG_TELEMETRY)` |  |
| 492 | [enosys](../../../xnu/bsd/kern/syscalls.master#L766) | `(!(CONFIG_TELEMETRY))` | Unavailable/reserved implementation (`enosys`). |
| 493 | [grab_pgo_data](../../../xnu/bsd/kern/syscalls.master#L769) · [mechanism](diagnostics-and-system-control.md#493-grab_pgo_data) | `(PGO)` |  |
| 493 | [enosys](../../../xnu/bsd/kern/syscalls.master#L771) | `(!(PGO))` | Unavailable/reserved implementation (`enosys`). |
| 494 | [persona](../../../xnu/bsd/kern/syscalls.master#L774) · [mechanism](processes-credentials-and-policy.md#494-persona) | `(CONFIG_PERSONAS)` |  |
| 494 | [enosys](../../../xnu/bsd/kern/syscalls.master#L776) | `(!(CONFIG_PERSONAS))` | Unavailable/reserved implementation (`enosys`). |
| 495 | [enosys](../../../xnu/bsd/kern/syscalls.master#L778) | `always` | Unavailable/reserved implementation (`enosys`). |
| 496 | [mach_eventlink_signal](../../../xnu/bsd/kern/syscalls.master#L779) · [mechanism](events-pthreads-and-async-io.md#496-mach_eventlink_signal) | `always` |  |
| 497 | [mach_eventlink_wait_until](../../../xnu/bsd/kern/syscalls.master#L780) · [mechanism](events-pthreads-and-async-io.md#497-mach_eventlink_wait_until) | `always` |  |
| 498 | [mach_eventlink_signal_wait_until](../../../xnu/bsd/kern/syscalls.master#L781) · [mechanism](events-pthreads-and-async-io.md#498-mach_eventlink_signal_wait_until) | `always` |  |
| 499 | [work_interval_ctl](../../../xnu/bsd/kern/syscalls.master#L782) · [mechanism](events-pthreads-and-async-io.md#499-work_interval_ctl) | `always` |  |
| 500 | [getentropy](../../../xnu/bsd/kern/syscalls.master#L783) · [mechanism](security-and-audit.md#500-getentropy) | `always` |  |
| 501 | [necp_open](../../../xnu/bsd/kern/syscalls.master#L785) · [mechanism](sockets-and-network-policy.md#501-necp_open) | `(NECP)` |  |
| 502 | [necp_client_action](../../../xnu/bsd/kern/syscalls.master#L786) · [mechanism](sockets-and-network-policy.md#502-necp_client_action) | `(NECP)` |  |
| 501 | [enosys](../../../xnu/bsd/kern/syscalls.master#L788) | `(!(NECP))` | Unavailable/reserved implementation (`enosys`). |
| 502 | [enosys](../../../xnu/bsd/kern/syscalls.master#L789) | `(!(NECP))` | Unavailable/reserved implementation (`enosys`). |
| 503 | [__nexus_open](../../../xnu/bsd/kern/syscalls.master#L792) · [mechanism](skywalk.md#503-__nexus_open) | `(SKYWALK)` |  |
| 504 | [__nexus_register](../../../xnu/bsd/kern/syscalls.master#L793) · [mechanism](skywalk.md#504-__nexus_register) | `(SKYWALK)` |  |
| 505 | [__nexus_deregister](../../../xnu/bsd/kern/syscalls.master#L794) · [mechanism](skywalk.md#505-__nexus_deregister) | `(SKYWALK)` |  |
| 506 | [__nexus_create](../../../xnu/bsd/kern/syscalls.master#L795) · [mechanism](skywalk.md#506-__nexus_create) | `(SKYWALK)` |  |
| 507 | [__nexus_destroy](../../../xnu/bsd/kern/syscalls.master#L796) · [mechanism](skywalk.md#507-__nexus_destroy) | `(SKYWALK)` |  |
| 508 | [__nexus_get_opt](../../../xnu/bsd/kern/syscalls.master#L797) · [mechanism](skywalk.md#508-__nexus_get_opt) | `(SKYWALK)` |  |
| 509 | [__nexus_set_opt](../../../xnu/bsd/kern/syscalls.master#L798) · [mechanism](skywalk.md#509-__nexus_set_opt) | `(SKYWALK)` |  |
| 510 | [__channel_open](../../../xnu/bsd/kern/syscalls.master#L799) · [mechanism](skywalk.md#510-__channel_open) | `(SKYWALK)` |  |
| 511 | [__channel_get_info](../../../xnu/bsd/kern/syscalls.master#L800) · [mechanism](skywalk.md#511-__channel_get_info) | `(SKYWALK)` |  |
| 512 | [__channel_sync](../../../xnu/bsd/kern/syscalls.master#L801) · [mechanism](skywalk.md#512-__channel_sync) | `(SKYWALK)` |  |
| 513 | [__channel_get_opt](../../../xnu/bsd/kern/syscalls.master#L802) · [mechanism](skywalk.md#513-__channel_get_opt) | `(SKYWALK)` |  |
| 514 | [__channel_set_opt](../../../xnu/bsd/kern/syscalls.master#L803) · [mechanism](skywalk.md#514-__channel_set_opt) | `(SKYWALK)` |  |
| 503 | [enosys](../../../xnu/bsd/kern/syscalls.master#L805) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 504 | [enosys](../../../xnu/bsd/kern/syscalls.master#L806) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 505 | [enosys](../../../xnu/bsd/kern/syscalls.master#L807) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 506 | [enosys](../../../xnu/bsd/kern/syscalls.master#L808) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 507 | [enosys](../../../xnu/bsd/kern/syscalls.master#L809) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 508 | [enosys](../../../xnu/bsd/kern/syscalls.master#L810) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 509 | [enosys](../../../xnu/bsd/kern/syscalls.master#L811) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 510 | [enosys](../../../xnu/bsd/kern/syscalls.master#L812) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 511 | [enosys](../../../xnu/bsd/kern/syscalls.master#L813) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 512 | [enosys](../../../xnu/bsd/kern/syscalls.master#L814) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 513 | [enosys](../../../xnu/bsd/kern/syscalls.master#L815) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 514 | [enosys](../../../xnu/bsd/kern/syscalls.master#L816) | `(!(SKYWALK))` | Unavailable/reserved implementation (`enosys`). |
| 515 | [sys_ulock_wait](../../../xnu/bsd/kern/syscalls.master#L818) · [mechanism](events-pthreads-and-async-io.md#515-sys_ulock_wait) | `always` |  |
| 516 | [sys_ulock_wake](../../../xnu/bsd/kern/syscalls.master#L819) · [mechanism](events-pthreads-and-async-io.md#516-sys_ulock_wake) | `always` |  |
| 517 | [fclonefileat](../../../xnu/bsd/kern/syscalls.master#L820) · [mechanism](filesystem-namespace.md#517-fclonefileat) | `always` |  |
| 518 | [fs_snapshot](../../../xnu/bsd/kern/syscalls.master#L821) · [mechanism](filesystem-mounts-and-control.md#518-fs_snapshot) | `always` |  |
| 519 | [enosys](../../../xnu/bsd/kern/syscalls.master#L822) | `always` | Unavailable/reserved implementation (`enosys`). |
| 520 | [terminate_with_payload](../../../xnu/bsd/kern/syscalls.master#L823) · [mechanism](signals-and-thread-control.md#520-terminate_with_payload) | `always` |  |
| 521 | [abort_with_payload](../../../xnu/bsd/kern/syscalls.master#L824) · [mechanism](signals-and-thread-control.md#521-abort_with_payload) | `always` |  |
| 522 | [necp_session_open](../../../xnu/bsd/kern/syscalls.master#L826) · [mechanism](sockets-and-network-policy.md#522-necp_session_open) | `(NECP)` |  |
| 523 | [necp_session_action](../../../xnu/bsd/kern/syscalls.master#L827) · [mechanism](sockets-and-network-policy.md#523-necp_session_action) | `(NECP)` |  |
| 522 | [enosys](../../../xnu/bsd/kern/syscalls.master#L829) | `(!(NECP))` | Unavailable/reserved implementation (`enosys`). |
| 523 | [enosys](../../../xnu/bsd/kern/syscalls.master#L830) | `(!(NECP))` | Unavailable/reserved implementation (`enosys`). |
| 524 | [setattrlistat](../../../xnu/bsd/kern/syscalls.master#L832) · [mechanism](filesystem-metadata.md#524-setattrlistat) | `always` |  |
| 525 | [net_qos_guideline](../../../xnu/bsd/kern/syscalls.master#L833) · [mechanism](sockets-and-network-policy.md#525-net_qos_guideline) | `always` |  |
| 526 | [fmount](../../../xnu/bsd/kern/syscalls.master#L834) · [mechanism](filesystem-mounts-and-control.md#526-fmount) | `always` |  |
| 527 | [ntp_adjtime](../../../xnu/bsd/kern/syscalls.master#L835) · [mechanism](time-and-accounting.md#527-ntp_adjtime) | `always` |  |
| 528 | [ntp_gettime](../../../xnu/bsd/kern/syscalls.master#L836) · [mechanism](time-and-accounting.md#528-ntp_gettime) | `always` |  |
| 529 | [os_fault_with_payload](../../../xnu/bsd/kern/syscalls.master#L837) · [mechanism](signals-and-thread-control.md#529-os_fault_with_payload) | `always` |  |
| 530 | [kqueue_workloop_ctl](../../../xnu/bsd/kern/syscalls.master#L838) · [mechanism](events-pthreads-and-async-io.md#530-kqueue_workloop_ctl) | `always` |  |
| 531 | [__mach_bridge_remote_time](../../../xnu/bsd/kern/syscalls.master#L839) · [mechanism](time-and-accounting.md#531-__mach_bridge_remote_time) | `always` |  |
| 532 | [coalition_ledger](../../../xnu/bsd/kern/syscalls.master#L841) · [mechanism](processes-credentials-and-policy.md#532-coalition_ledger) | `(CONFIG_COALITIONS)` |  |
| 532 | [enosys](../../../xnu/bsd/kern/syscalls.master#L843) | `(!(CONFIG_COALITIONS))` | Unavailable/reserved implementation (`enosys`). |
| 533 | [log_data](../../../xnu/bsd/kern/syscalls.master#L845) · [mechanism](diagnostics-and-system-control.md#533-log_data) | `always` |  |
| 534 | [memorystatus_available_memory](../../../xnu/bsd/kern/syscalls.master#L846) · [mechanism](virtual-memory.md#534-memorystatus_available_memory) | `always` |  |
| 535 | [objc_bp_assist_cfg_np](../../../xnu/bsd/kern/syscalls.master#L847) · [mechanism](diagnostics-and-system-control.md#535-objc_bp_assist_cfg_np) | `always` |  |
| 536 | [shared_region_map_and_slide_2_np](../../../xnu/bsd/kern/syscalls.master#L848) · [mechanism](virtual-memory.md#536-shared_region_map_and_slide_2_np) | `always` |  |
| 537 | [pivot_root](../../../xnu/bsd/kern/syscalls.master#L849) · [mechanism](filesystem-mounts-and-control.md#537-pivot_root) | `always` |  |
| 538 | [task_inspect_for_pid](../../../xnu/bsd/kern/syscalls.master#L850) · [mechanism](processes-credentials-and-policy.md#538-task_inspect_for_pid) | `always` |  |
| 539 | [task_read_for_pid](../../../xnu/bsd/kern/syscalls.master#L851) · [mechanism](processes-credentials-and-policy.md#539-task_read_for_pid) | `always` |  |
| 540 | [sys_preadv](../../../xnu/bsd/kern/syscalls.master#L852) · [mechanism](files-and-descriptors.md#540-sys_preadv) | `always` |  |
| 541 | [sys_pwritev](../../../xnu/bsd/kern/syscalls.master#L853) · [mechanism](files-and-descriptors.md#541-sys_pwritev) | `always` |  |
| 542 | [sys_preadv_nocancel](../../../xnu/bsd/kern/syscalls.master#L854) · [mechanism](files-and-descriptors.md#542-sys_preadv_nocancel) | `always` |  |
| 543 | [sys_pwritev_nocancel](../../../xnu/bsd/kern/syscalls.master#L855) · [mechanism](files-and-descriptors.md#543-sys_pwritev_nocancel) | `always` |  |
| 544 | [sys_ulock_wait2](../../../xnu/bsd/kern/syscalls.master#L856) · [mechanism](events-pthreads-and-async-io.md#544-sys_ulock_wait2) | `always` |  |
| 545 | [proc_info_extended_id](../../../xnu/bsd/kern/syscalls.master#L857) · [mechanism](processes-credentials-and-policy.md#545-proc_info_extended_id) | `always` |  |
| 546 | [tracker_action](../../../xnu/bsd/kern/syscalls.master#L859) · [mechanism](sockets-and-network-policy.md#546-tracker_action) | `(SOCKETS)` |  |
| 546 | [nosys](../../../xnu/bsd/kern/syscalls.master#L861) | `(!(SOCKETS))` | Unavailable/reserved implementation (`nosys`). |
| 547 | [debug_syscall_reject](../../../xnu/bsd/kern/syscalls.master#L863) · [mechanism](diagnostics-and-system-control.md#547-debug_syscall_reject) | `always` |  |
| 548 | [sys_debug_syscall_reject_config](../../../xnu/bsd/kern/syscalls.master#L864) · [mechanism](diagnostics-and-system-control.md#548-sys_debug_syscall_reject_config) | `always` |  |
| 549 | [graftdmg](../../../xnu/bsd/kern/syscalls.master#L865) · [mechanism](filesystem-mounts-and-control.md#549-graftdmg) | `always` |  |
| 550 | [map_with_linking_np](../../../xnu/bsd/kern/syscalls.master#L866) · [mechanism](virtual-memory.md#550-map_with_linking_np) | `always` |  |
| 551 | [freadlink](../../../xnu/bsd/kern/syscalls.master#L867) · [mechanism](filesystem-namespace.md#551-freadlink) | `always` |  |
| 552 | [sys_record_system_event](../../../xnu/bsd/kern/syscalls.master#L868) · [mechanism](diagnostics-and-system-control.md#552-sys_record_system_event) | `always` |  |
| 553 | [mkfifoat](../../../xnu/bsd/kern/syscalls.master#L869) · [mechanism](filesystem-namespace.md#553-mkfifoat) | `always` |  |
| 554 | [mknodat](../../../xnu/bsd/kern/syscalls.master#L870) · [mechanism](filesystem-namespace.md#554-mknodat) | `always` |  |
| 555 | [ungraftdmg](../../../xnu/bsd/kern/syscalls.master#L871) · [mechanism](filesystem-mounts-and-control.md#555-ungraftdmg) | `always` |  |
| 556 | [sys_coalition_policy_set](../../../xnu/bsd/kern/syscalls.master#L873) · [mechanism](processes-credentials-and-policy.md#556-sys_coalition_policy_set) | `(CONFIG_COALITIONS)` |  |
| 557 | [sys_coalition_policy_get](../../../xnu/bsd/kern/syscalls.master#L874) · [mechanism](processes-credentials-and-policy.md#557-sys_coalition_policy_get) | `(CONFIG_COALITIONS)` |  |
| 556 | [enosys](../../../xnu/bsd/kern/syscalls.master#L876) | `(!(CONFIG_COALITIONS))` | Unavailable/reserved implementation (`enosys`). |
| 557 | [enosys](../../../xnu/bsd/kern/syscalls.master#L877) | `(!(CONFIG_COALITIONS))` | Unavailable/reserved implementation (`enosys`). |

## Reconciliation

- Distinct syscall numbers: **558**, from **0** through **557**.
- Declaration alternatives: **669**.
- Non-stub declarations with authored purpose and implementation mechanism: **455**.
- `nosys`/`enosys` alternatives: **214**.
- These are source declarations across configurations, not the enabled calls in one running kernel.
