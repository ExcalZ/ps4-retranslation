#!/bin/bash

version="0.0.5b"

this="${0##*/}"

usage="USAGE: ${this} <assembly file> <output> [output] [... [outputN]]
       ${this} --help"

fixheader="`dirname $0`/fixheader.py"
ips="`dirname $0`/lipx.py"

help="$this for disassembled SEGA Mega Drive / Genesis Phantasy Star games.
Version ${version}
By zucca@kahvipannu.com
License: BSD

Major dependencies are
    - asl, the macro assembler
    - gawk 4.1.1 or newer for inline patching
    - gcc only for compiling the p2bin
    - BSDiff, Xdelta, bdiff for support of patch file creation
    - If you want to use built-in fixheader, you need Python 3.

Note that this script may reside anywhere in the filesystem.
Also running this script outside of the directory where the assembly is allowed.

$usage

Where output may be *.bin *.bsdiff *.xdelta *.bdiff ...

Switches:
    Location of p2bin.
    --p2bin <p2bin executable>

    See README.adoc 'Known limitations' -section for this.
    --fixheader <fixheader executable>

    Does not delete temporary files.
    --keep-temp
    (${this} still keeps temporary files in some cases where process has failed.)
"

# Sets the name of the assembly log file if not set from the environment.
: ${ASlog:="AS.log"}


msg() { echo -e "$*"; }

warn() {
    echo -e "$*" 1>&2
}

# Maybe overkill for such a simple script
# but we have now a function for exiting.
errexit() {
    if echo "$1" | grep -E '^[0-9]+$' > /dev/null
    then
	# First argument was a number. We use it as an exit code.
        ec="$1"
        shift
    fi
    warn "$*"
    exit "${ec:=1}"
}

check_dep() {
    if [ -x "$(which "$1")" ]
    then
        return 0
    elif [ "$2" = "die" ]
    then
        errexit 127 "Aborting: '$1' cannot be found or isn't an executable."
    else
        return 127
    fi
}

# Path patching using awk.
# While we're at it replace paths with absolute ones.
# Why? I didn't find any way to tell asl
# from which diretory to search for includes.
path_patch() {
    # We are using gawk. Would maybe be better to use POSIX awk instead...
    gawk -i inplace -v "includedir=${includedir}" '{if (/b?include\s+"/) { sub("\"","\"" includedir "/"); gsub("\\\\","/") } print }' "$@"
}

# Creates the final binary into the temp directory
build_bin() {
    if ! [ -e "$temp_bin" ]
    then
        "$p2bin" "$temp_p" "$temp_bin" "$temp_h" > /dev/null \
            && msg "Succesfully created the binary." \
            || errexit "p2bin failed to create the binary."
        fix_bin_header "$temp_bin"
    else
        # We already have the binary. Return succesfully.
        return 0
    fi
}

# Be careful. fix_bin_header is this function and fixheader is the binary.
fix_bin_header() {
    # Choose if we want to fix the header.
    if [ "$fixheader" ] && [ ! "$nohfix" ]
    then
        "$fixheader" "$1" && msg "Fixed the header..." || warn "Header fixing failed!"
    else
         warn "Binary header left unfixed."
    fi
}

### Patch creation functions
# Every function takes <oldfile> <newfile> <patchfile>

# Perhaps the most efficient binary diff algo there is.
create_bsdiff() {
    check_dep "${bsdiff:="bsdiff"}" die && "$bsdiff" "$1" "$2" "$3" || warn "BSDiff failed."
    msg "BSDiff created to '$3'..."
}

# Xdelta is one of the most common binary diff programs.
create_xdelta() {
    check_dep "${xdelta:="xdelta3"}" die && "$xdelta" -e -S djw -9 -s "$1" "$2" "$3"  || warn "Xdelta failed."
    msg "Xdelta created to '$3'..."
}

# BDelta. https://github.com/jjwhitney/BDelta
create_bdelta() {
    check_dep "${bdelta:="bdelta"}" die && "$bdelta" "$1" "$2" "$3" || warn "bdelta failed."
    msg "bdiff created to '$3'..."
}

# IPS is a common format too. romhacking.net users might want to use this.
create_ips() {
    check_dep "${ips}" die && "$ips" -c "$1" "$2" || warn "ips failed."
    mv "$2.ips" "$3"
#    warn "ips patches not implemented yet."
#    errexit "If you know a ips patch creation cli utility for Linux, please post an issue at:\nhttps://github.com/Zuccace/mdps-asm-builder/issues"
}

### Go trough CLI switches.
while [ "${1:0:1}" = "-" ]
do
    case "$1" in
        --p2bin)
            [ "$2" ] && check_dep "$2" die
            p2bin="$2"
            shift
        ;;
        --fixheader)
            [ "$2" ] && check_dep "$2" die
            fixheader="$2"
            shift
        ;;
        --orig-bin)
            [ -e "$2" ] && orig_bin="$2" || errexit "No such file '${2}'."
        ;;
        # Undocumented. Will use later.
        --no-header-fix)
            nohfix=1
        ;;
        --keep-temp)
            keeptemp=1
        ;;
        --help)
            echo "${help}"
            exit 0
        ;;
        --)
            shift
            break
        ;;
        *)
            warn "Not a _slightest_ clue what to do with that $1 switch of yours."
            errexit "Tip. Use '--' to break switch searching. Exiting..."
        ;;
    esac
    shift
done

# Test arguments and existence of provided assembly file.
[ "$1" ] || errexit "${usage}"
if [ ! "$2" ]
then
    errexit "No output file(s) specified."
fi

workdir="$(mktemp -td AS_tmp_XXXXXX)"

# Set include dir to the directory where the assembly file is in.
includedir="$(readlink -f "$1")"
includedir="${includedir%/*}"

temp_log="${workdir}/${ASlog##*/}"
temp_p="${workdir}/out.p"
temp_h="${workdir}/out.h"
temp_bin="${workdir}/out.bin"

# Guess the location of original binary (for patches) if not set already.
# So by default it's the same as the main assembly file with extension changed to 'bin'.
: ${orig_bin:="${1%.*}original.bin"}

# Copy files to our temporary directory.
cp "$1" "$workdir"

asmfile="${workdir}/${1##*/}"

# Patch and compile the assembly.
path_patch "$asmfile" && msg "Path patch applied..." || errexit "Patching failed. '$tempdir' -directory is left undeleted."
"${asl:="asl"}" -xx -c -A -l -shareout "$temp_h" -o "$temp_p" "$asmfile" > "$temp_log" 2>&1 \
    && msg Source compiled... \
    || errexit "Source compiling failed. Temporary files are left intact inside '${workdir}' -directory."

# Find source and compile the p2bin program if needed.
if ! [ -e "${p2bin:=${includedir}/p2bin}" ]
then
    p2bin_source="$(find "$includedir" -name '*p2bin.c')"
    if [ "$(wc -l <<< "$p2bin_source")" -eq "1" ]
    then
        if gcc -O3 -w -o "$p2bin" "$p2bin_source"
        then
            msg "p2bin compiled..."
        else
            rm -r "$workdir"
            warn "Compiling p2bin failed."
            [ -e "$p2bin" ] && rm "$p2bin"
            errexit "Aborting..."
        fi
    fi
fi

# Combine all the files to form the binary
build_bin

shift
# Now we have only the output files left on the command line.
# Let's roll!

while [ "$1" ]
do

    ext="${1##*.}" # Filename extension

    # At least busybox ash doesn't support <<< redirection. That's why the echo.
    case "$(echo "$ext" | tr '[:upper:]' '[:lower:]')" in # lovercase
        bin)
            out_bin="$1"
        ;;
        bsdiff)
            create_bsdiff "$orig_bin" "$temp_bin" "$1"
        ;;
        xdelta)
            create_xdelta "$orig_bin" "$temp_bin" "$1"
        ;;
        bdiff)
            create_bdiff "$orig_bin" "$temp_bin" "$1"
        ;;
        ips)
            create_ips "$orig_bin" "$temp_bin" "$1"
        ;;
        *)
            warn "File type on '${ext}' is unknown. Skipping..."
        ;;
    esac
shift
done

[ "$out_bin" ] && mv "$temp_bin" "$out_bin" && msg "Binary is located at '${out_bin}'."

[ "$keeptemp" ] && msg "Temp files left into '${workdir}'" || rm -r "$workdir"
