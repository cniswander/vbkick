# Place for official vbkick OS templates

## Overview

By default templates define Vagrant Base Boxes, so in each template vagrant user is created.

## templates structure (good practice)

```
    .
    ├── RedHat6
    │   ├── definition.cfg
    │   ├── definition-6.2-x86_64-noX.cfg
    │   ├── definition-6.3-x86_64-noX.cfg
    │   ├── definition-6.4-x86_64-noX.cfg
    │   ├── kickstart
    │   │   └── <redhat-6.3-x86_64-noX.cfg, redhat-6.4-x86_64-docker.cfg, ...>
    │   ├── validate
    │   │   └── <adm_features.sh, adm_context.txt, adm_envrc, test_puppet.sh, test_ruby.sh, test_virtualbox.sh, test_vagrant, ....sh >
    │   └── postinstall
    │       └── <adm_postinstall.sh, adm_context.txt, adm_envrc, base.sh, cleanup.sh, puppet.sh, ruby.sh, virtualbox.sh, ....sh >
    ├── RedHat5
    │   ├── definition.cfg
    │   ├── definition-5.5-x86_64-noX.cfg
    │   ├── definition-5.6-x86_64-noX.cfg
    │   ├── definition-5.9-x86_64-noX.cfg
    │   ├── kickstart
    │   │   └── <redhat-5.6-x86_64-noX.cfg, redhat-5.9-i386-desktop.cfg, ...>
    │   ├── validate
    │   │   └── <adm_features.sh, adm_context.txt, adm_envrc, test_puppet.sh, test_ruby.sh, test_virtualbox.sh, test_vagrant, ....sh >
    │   └── postinstall
    │       └── <adm_postinstall.sh, adm_context.txt, adm_envrc, base.sh, cleanup.sh, puppet.sh, ruby.sh, virtualbox.sh, ....sh >
    └── Debian7
        ├── definition.cfg
        ├── definition-7.1-i386-KDE.cfg
        ├── definition-7.1-x86_64-noX.cfg
        ├── kickstart
        │   └── <Debian-7.1-x86_64-noX.cfg, Debian-7.1-i386-desktop.cfg, ...>
        ├── validate
        │   └── <adm_features.sh, adm_context.txt, adm_envrc, test_puppet.sh, test_ruby.sh, test_virtualbox.sh, test_vagrant, ....sh >
        └── postinstall
            └── <adm_postinstall.sh, adm_context.txt, adm_envrc, base.sh, cleanup.sh, puppet.sh, ruby.sh, virtualbox.sh, ....sh >
```

```
    drwxr-xr-x  .
    drwxr-xr-x. ..
    lrwxrwxrwx  definition.cfg -> definition-6.4-x86_64-noX.cfg
    -rw-r--r--  definition-6.3-i386-noX.cfg
    -rw-r--r--  definition-6.3-x86_64-noX.cfg
    -rw-r--r--  definition-6.4-i386-noX.cfg
    -rw-r--r--  definition-6.4-x86_64-noX.cfg
    drwxr-xr-x  iso
    drwxr-xr-x  keys
    drwxr-xr-x  kickstart
    drwxr-xr-x  postinstall
    drwxr-xr-x  validate
    -rw-r--r--  LICENSE
    -rw-r--r--  README.md
```

howto update symlink:
```
    ln -fs definition-6.4-i386.cfg definition.cfg
```

Description:
 - postinstall dir contain all scripts run during postinstall process
 - validate dir contain all scripts run during validate process
 - kickstart dir contain all files used during bootstrap process
 - each file in kickstart (e.g. ks.cfg/preseed.cfg) has descriptive names (`<OS_NAME>-<VERSION>-<ARCH>-<SPEC_DESC>.cfg`) e.g.: redhat-6.3-x86_64-noX.cfg, redhat-6.4-x86_64-docker.cfg, debian-7.0-x86_64-desktop.cfg
 - **definition.cfg is symlink** to default vbkick definition
 - each definition has descriptive name e.g. definition-6.3-x86_64-noX.cfg, definition-6.4-x86_64-noX.cfg, definition-6.5-x86_64-beta.cfg
 - each template take care about "big" OS release, e.g. RedHat6, Redhat5, Debian7, Debian6
 - OS ISOs and SSH keys are not included
 - README.md and LICENSE files are required
 - Note (good practice): If you create Vagrant base box then use vagrant user and vagrant ssh keys, not create thousands other accounts (like vbkick, veewee...)

## Maintenance info

 - Debian6 "Squeeze" (End of life - May 2014)
 - Fedora18 (End of life - Early 2014)
