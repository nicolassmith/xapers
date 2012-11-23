#
# Copyright (c) 2005 Junio C Hamano
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/ .

if [ ${BASH_VERSINFO[0]} -lt 4 ]; then
    echo "Error: The notmuch test suite requires a bash version >= 4.0"
    echo "due to use of associative arrays within the test suite."
    echo "Please try again with a newer bash (or help us fix the"
    echo "test suite to be more portable). Thanks."
    exit 1
fi

# if --tee was passed, write the output not only to the terminal, but
# additionally to the file test-results/$BASENAME.out, too.
case "$GIT_TEST_TEE_STARTED, $* " in
done,*)
	# do not redirect again
	;;
*' --tee '*|*' --va'*)
	mkdir -p test-results
	BASE=test-results/$(basename "$0" .sh)
	(GIT_TEST_TEE_STARTED=done ${SHELL-sh} "$0" "$@" 2>&1;
	 echo $? > $BASE.exit) | tee $BASE.out
	test "$(cat $BASE.exit)" = 0
	exit
	;;
esac

# Keep the original TERM for say_color and test_emacs
ORIGINAL_TERM=$TERM

# For repeatability, reset the environment to known value.
LANG=C
LC_ALL=C
PAGER=cat
TZ=UTC
TERM=dumb
export LANG LC_ALL PAGER TERM TZ
GIT_TEST_CMP=${GIT_TEST_CMP:-diff -u}
TEST_EMACS=${TEST_EMACS:-${EMACS:-emacs}}

# Protect ourselves from common misconfiguration to export
# CDPATH into the environment
unset CDPATH

unset GREP_OPTIONS

# Convenience
#
# A regexp to match 5 and 40 hexdigits
_x05='[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
_x40="$_x05$_x05$_x05$_x05$_x05$_x05$_x05$_x05"

_x04='[0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
_x32="$_x04$_x04$_x04$_x04$_x04$_x04$_x04$_x04"

# Each test should start with something like this, after copyright notices:
#
# test_description='Description of this test...
# This test checks if command xyzzy does the right thing...
# '
# . ./test-lib.sh
[ "x$ORIGINAL_TERM" != "xdumb" ] && (
		TERM=$ORIGINAL_TERM &&
		export TERM &&
		[ -t 1 ] &&
		tput bold >/dev/null 2>&1 &&
		tput setaf 1 >/dev/null 2>&1 &&
		tput sgr0 >/dev/null 2>&1
	) &&
	color=t

while test "$#" -ne 0
do
	case "$1" in
	-d|--d|--de|--deb|--debu|--debug)
		debug=t; shift ;;
	-i|--i|--im|--imm|--imme|--immed|--immedi|--immedia|--immediat|--immediate)
		immediate=t; shift ;;
	-l|--l|--lo|--lon|--long|--long-|--long-t|--long-te|--long-tes|--long-test|--long-tests)
		GIT_TEST_LONG=t; export GIT_TEST_LONG; shift ;;
	-h|--h|--he|--hel|--help)
		help=t; shift ;;
	-v|--v|--ve|--ver|--verb|--verbo|--verbos|--verbose)
		verbose=t; shift ;;
	-q|--q|--qu|--qui|--quie|--quiet)
		quiet=t; shift ;;
	--with-dashes)
		with_dashes=t; shift ;;
	--no-color)
		color=; shift ;;
	--no-python)
		# noop now...
		shift ;;
	--va|--val|--valg|--valgr|--valgri|--valgrin|--valgrind)
		valgrind=t; verbose=t; shift ;;
	--tee)
		shift ;; # was handled already
	--root=*)
		root=$(expr "z$1" : 'z[^=]*=\(.*\)')
		shift ;;
	*)
		echo "error: unknown test option '$1'" >&2; exit 1 ;;
	esac
done

if test -n "$debug"; then
    print_subtest () {
	printf " %-4s" "[$((test_count - 1))]"
    }
else
    print_subtest () {
	true
    }
fi

if test -n "$color"; then
	say_color () {
		(
		TERM=$ORIGINAL_TERM
		export TERM
		case "$1" in
			error) tput bold; tput setaf 1;; # bold red
			skip)  tput bold; tput setaf 2;; # bold green
			pass)  tput setaf 2;;            # green
			info)  tput setaf 3;;            # brown
			*) test -n "$quiet" && return;;
		esac
		shift
		printf " "
		printf "$@"
		tput sgr0
		print_subtest
		)
	}
else
	say_color() {
		test -z "$1" && test -n "$quiet" && return
		shift
		printf " "
		printf "$@"
		print_subtest
	}
fi

error () {
	say_color error "error: $*\n"
	GIT_EXIT_OK=t
	exit 1
}

say () {
	say_color info "$*"
}

test "${test_description}" != "" ||
error "Test script did not set test_description."

if test "$help" = "t"
then
	echo "Tests ${test_description}"
	exit 0
fi

echo $(basename "$0"): "Testing ${test_description}"

exec 5>&1

test_failure=0
test_count=0
test_fixed=0
test_broken=0
test_success=0

die () {
	code=$?
	rm -rf "$TEST_TMPDIR"
	if test -n "$GIT_EXIT_OK"
	then
		exit $code
	else
		echo >&5 "FATAL: Unexpected exit with code $code"
		exit 1
	fi
}

GIT_EXIT_OK=
# Note: TEST_TMPDIR *NOT* exported!
TEST_TMPDIR=$(mktemp -d "${TMPDIR:-/tmp}/test-$$.XXXXXX")
trap 'die' EXIT

test_decode_color () {
	sed	-e 's/.\[1m/<WHITE>/g' \
		-e 's/.\[31m/<RED>/g' \
		-e 's/.\[32m/<GREEN>/g' \
		-e 's/.\[33m/<YELLOW>/g' \
		-e 's/.\[34m/<BLUE>/g' \
		-e 's/.\[35m/<MAGENTA>/g' \
		-e 's/.\[36m/<CYAN>/g' \
		-e 's/.\[m/<RESET>/g'
}

q_to_nul () {
	perl -pe 'y/Q/\000/'
}

q_to_cr () {
	tr Q '\015'
}

append_cr () {
	sed -e 's/$/Q/' | tr Q '\015'
}

remove_cr () {
	tr '\015' Q | sed -e 's/Q$//'
}

test_begin_subtest ()
{
    if [ -n "$inside_subtest" ]; then
	exec 1>&6 2>&7		# Restore stdout and stderr
	error "bug in test script: Missing test_expect_equal in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}"
    fi
    test_subtest_name="$1"
    test_reset_state_
    # Remember stdout and stderr file descriptors and redirect test
    # output to the previously prepared file descriptors 3 and 4 (see
    # below)
    if test "$verbose" != "t"; then exec 4>test.output 3>&4; fi
    exec 6>&1 7>&2 >&3 2>&4
    inside_subtest=t
}

# Pass test if two arguments match
#
# Note: Unlike all other test_expect_* functions, this function does
# not accept a test name. Instead, the caller should call
# test_begin_subtest before calling this function in order to set the
# name.
test_expect_equal ()
{
	exec 1>&6 2>&7		# Restore stdout and stderr
	inside_subtest=
	test "$#" = 3 && { prereq=$1; shift; } || prereq=
	test "$#" = 2 ||
	error "bug in the test script: not 2 or 3 parameters to test_expect_equal"

	output="$1"
	expected="$2"
	if ! test_skip "$test_subtest_name"
	then
		if [ "$output" = "$expected" ]; then
			test_ok_ "$test_subtest_name"
		else
			testname=$this_test.$test_count
			echo "$expected" > $testname.expected
			echo "$output" > $testname.output
			test_failure_ "$test_subtest_name" "$(diff -u $testname.expected $testname.output)"
		fi
    fi
}

# Like test_expect_equal, but takes two filenames.
test_expect_equal_file ()
{
	exec 1>&6 2>&7		# Restore stdout and stderr
	inside_subtest=
	test "$#" = 3 && { prereq=$1; shift; } || prereq=
	test "$#" = 2 ||
	error "bug in the test script: not 2 or 3 parameters to test_expect_equal"

	output="$1"
	expected="$2"
	if ! test_skip "$test_subtest_name"
	then
		if diff -q "$expected" "$output" >/dev/null ; then
			test_ok_ "$test_subtest_name"
		else
			testname=$this_test.$test_count
			cp "$output" $testname.output
			cp "$expected" $testname.expected
			test_failure_ "$test_subtest_name" "$(diff -u $testname.expected $testname.output)"
		fi
    fi
}

# Like test_expect_equal, but arguments are JSON expressions to be
# canonicalized before diff'ing.  If an argument cannot be parsed, it
# is used unchanged so that there's something to diff against.
test_expect_equal_json () {
    output=$(echo "$1" | python -mjson.tool || echo "$1")
    expected=$(echo "$2" | python -mjson.tool || echo "$2")
    shift 2
    test_expect_equal "$output" "$expected" "$@"
}

# Use test_set_prereq to tell that a particular prerequisite is available.
# The prerequisite can later be checked for in two ways:
#
# - Explicitly using test_have_prereq.
#
# - Implicitly by specifying the prerequisite tag in the calls to
#   test_expect_{success,failure,code}.
#
# The single parameter is the prerequisite tag (a simple word, in all
# capital letters by convention).
test_set_prereq () {
	satisfied="$satisfied$1 "
}
satisfied=" "

test_have_prereq () {
	case $satisfied in
	*" $1 "*)
		: yes, have it ;;
	*)
		! : nope ;;
	esac
}

# declare prerequisite for the given external binary
test_declare_external_prereq () {
	binary="$1"
	test "$#" = 2 && name=$2 || name="$binary(1)"

	hash $binary 2>/dev/null || eval "
	test_missing_external_prereq_${binary}_=t
$binary () {
	echo -n \"\$test_subtest_missing_external_prereqs_ \" | grep -qe \" $name \" ||
	test_subtest_missing_external_prereqs_=\"\$test_subtest_missing_external_prereqs_ $name\"
	false
}"
}

# Explicitly require external prerequisite.  Useful when binary is
# called indirectly (e.g. from emacs).
# Returns success if dependency is available, failure otherwise.
test_require_external_prereq () {
	binary="$1"
	if [ "$(eval echo -n \$test_missing_external_prereq_${binary}_)" = t ]; then
		# dependency is missing, call the replacement function to note it
		eval "$binary"
	else
		true
	fi
}

# You are not expected to call test_ok_ and test_failure_ directly, use
# the text_expect_* functions instead.

test_ok_ () {
	if test "$test_subtest_known_broken_" = "t"; then
		test_known_broken_ok_ "$@"
		return
	fi
	test_success=$(($test_success + 1))
	say_color pass "%-6s" "PASS"
	echo " $@"
}

test_failure_ () {
	if test "$test_subtest_known_broken_" = "t"; then
		test_known_broken_failure_ "$@"
		return
	fi
	test_failure=$(($test_failure + 1))
	test_failure_message_ "FAIL" "$@"
	test "$immediate" = "" || { GIT_EXIT_OK=t; exit 1; }
	return 1
}

test_failure_message_ () {
	say_color error "%-6s" "$1"
	echo " $2"
	shift 2
	echo "$@" | sed -e 's/^/	/'
	if test "$verbose" != "t"; then cat test.output; fi
}

test_known_broken_ok_ () {
	test_reset_state_
	test_fixed=$(($test_fixed+1))
	say_color pass "%-6s" "FIXED"
	echo " $@"
}

test_known_broken_failure_ () {
	test_reset_state_
	test_broken=$(($test_broken+1))
	test_failure_message_ "BROKEN" "$@"
	return 1
}

test_debug () {
	test "$debug" = "" || eval "$1"
}

test_run_ () {
	test_cleanup=:
	if test "$verbose" != "t"; then exec 4>test.output 3>&4; fi
	eval >&3 2>&4 "$1"
	eval_ret=$?
	eval >&3 2>&4 "$test_cleanup"
	return 0
}

test_skip () {
	test_count=$(($test_count+1))
	to_skip=
	for skp in $XAPERS_SKIP_TESTS
	do
		case $this_test.$test_count in
		$skp)
			to_skip=t
		esac
	done
	if test -z "$to_skip" && test -n "$prereq" &&
	   ! test_have_prereq "$prereq"
	then
		to_skip=t
	fi
	case "$to_skip" in
	t)
		test_report_skip_ "$@"
		;;
	*)
		test_check_missing_external_prereqs_ "$@"
		;;
	esac
}

test_check_missing_external_prereqs_ () {
	if test -n "$test_subtest_missing_external_prereqs_"; then
		say_color skip >&1 "missing prerequisites:"
		echo "$test_subtest_missing_external_prereqs_" >&1
		test_report_skip_ "$@"
	else
		false
	fi
}

test_report_skip_ () {
	test_reset_state_
	say_color skip >&3 "skipping test:"
	echo " $@" >&3
	say_color skip "%-6s" "SKIP"
	echo " $1"
}

test_subtest_known_broken () {
	test_subtest_known_broken_=t
}

test_expect_success () {
	test "$#" = 3 && { prereq=$1; shift; } || prereq=
	test "$#" = 2 ||
	error "bug in the test script: not 2 or 3 parameters to test-expect-success"
	test_reset_state_
	if ! test_skip "$@"
	then
		test_run_ "$2"
		run_ret="$?"
		# test_run_ may update missing external prerequisites
		test_check_missing_external_prereqs_ "$@" ||
		if [ "$run_ret" = 0 -a "$eval_ret" = 0 ]
		then
			test_ok_ "$1"
		else
			test_failure_ "$@"
		fi
	fi
}

test_expect_code () {
	test "$#" = 4 && { prereq=$1; shift; } || prereq=
	test "$#" = 3 ||
	error "bug in the test script: not 3 or 4 parameters to test-expect-code"
	test_reset_state_
	if ! test_skip "$@"
	then
		test_run_ "$3"
		run_ret="$?"
		# test_run_ may update missing external prerequisites,
		test_check_missing_external_prereqs_ "$@" ||
		if [ "$run_ret" = 0 -a "$eval_ret" = "$1" ]
		then
			test_ok_ "$2"
		else
			test_failure_ "$@"
		fi
	fi
}

# test_external runs external test scripts that provide continuous
# test output about their progress, and succeeds/fails on
# zero/non-zero exit code.  It outputs the test output on stdout even
# in non-verbose mode, and announces the external script with "* run
# <n>: ..." before running it.  When providing relative paths, keep in
# mind that all scripts run in "trash directory".
# Usage: test_external description command arguments...
# Example: test_external 'Perl API' perl ../path/to/test.pl
test_external () {
	test "$#" = 4 && { prereq=$1; shift; } || prereq=
	test "$#" = 3 ||
	error >&5 "bug in the test script: not 3 or 4 parameters to test_external"
	descr="$1"
	shift
	test_reset_state_
	if ! test_skip "$descr" "$@"
	then
		# Announce the script to reduce confusion about the
		# test output that follows.
		say_color "" " run $test_count: $descr ($*)"
		# Run command; redirect its stderr to &4 as in
		# test_run_, but keep its stdout on our stdout even in
		# non-verbose mode.
		"$@" 2>&4
		if [ "$?" = 0 ]
		then
			test_ok_ "$descr"
		else
			test_failure_ "$descr" "$@"
		fi
	fi
}

# Like test_external, but in addition tests that the command generated
# no output on stderr.
test_external_without_stderr () {
	# The temporary file has no (and must have no) security
	# implications.
	tmp="$TMPDIR"; if [ -z "$tmp" ]; then tmp=/tmp; fi
	stderr="$tmp/git-external-stderr.$$.tmp"
	test_external "$@" 4> "$stderr"
	[ -f "$stderr" ] || error "Internal error: $stderr disappeared."
	descr="no stderr: $1"
	shift
	if [ ! -s "$stderr" ]; then
		rm "$stderr"
		test_ok_ "$descr"
	else
		if [ "$verbose" = t ]; then
			output=`echo; echo Stderr is:; cat "$stderr"`
		else
			output=
		fi
		# rm first in case test_failure exits.
		rm "$stderr"
		test_failure_ "$descr" "$@" "$output"
	fi
}

# This is not among top-level (test_expect_success)
# but is a prefix that can be used in the test script, like:
#
#	test_expect_success 'complain and die' '
#           do something &&
#           do something else &&
#	    test_must_fail git checkout ../outerspace
#	'
#
# Writing this as "! git checkout ../outerspace" is wrong, because
# the failure could be due to a segv.  We want a controlled failure.
test_must_fail () {
	"$@"
	test $? -gt 0 -a $? -le 129 -o $? -gt 192
}

# test_cmp is a helper function to compare actual and expected output.
# You can use it like:
#
#	test_expect_success 'foo works' '
#		echo expected >expected &&
#		foo >actual &&
#		test_cmp expected actual
#	'
#
# This could be written as either "cmp" or "diff -u", but:
# - cmp's output is not nearly as easy to read as diff -u
# - not all diff versions understand "-u"
test_cmp() {
	$GIT_TEST_CMP "$@"
}

# This function can be used to schedule some commands to be run
# unconditionally at the end of the test to restore sanity:
#
#	test_expect_success 'test core.capslock' '
#		git config core.capslock true &&
#		test_when_finished "git config --unset core.capslock" &&
#		hello world
#	'
#
# That would be roughly equivalent to
#
#	test_expect_success 'test core.capslock' '
#		git config core.capslock true &&
#		hello world
#		git config --unset core.capslock
#	'
#
# except that the greeting and config --unset must both succeed for
# the test to pass.
test_when_finished () {
	test_cleanup="{ $*
		} && (exit \"\$eval_ret\"); eval_ret=\$?; $test_cleanup"
}

test_done () {
	GIT_EXIT_OK=t
	test_results_dir="$TEST_DIRECTORY/test-results"
	mkdir -p "$test_results_dir"
	test_results_path="$test_results_dir/${0%.sh}-$$"

	echo "total $test_count" >> $test_results_path
	echo "success $test_success" >> $test_results_path
	echo "fixed $test_fixed" >> $test_results_path
	echo "broken $test_broken" >> $test_results_path
	echo "failed $test_failure" >> $test_results_path
	echo "" >> $test_results_path

	echo

	[ -n "$EMACS_SERVER" ] && test_emacs '(kill-emacs)'

	if [ "$test_failure" = "0" ]; then
	    if [ "$test_broken" = "0" ]; then
		rm -rf "$remove_tmp"
	    fi
	    exit 0
	else
	    exit 1
	fi
}

test_python() {
	export LD_LIBRARY_PATH=$TEST_DIRECTORY/../lib
	export PYTHONPATH=$TEST_DIRECTORY/../bindings/python

	# Some distros (e.g. Arch Linux) ship Python 2.* as /usr/bin/python2,
	# most others as /usr/bin/python. So first try python2, and fallback to
	# python if python2 doesn't exist.
	cmd=python2
	[[ "$test_missing_external_prereq_python2_" = t ]] && cmd=python

	(echo "import sys; _orig_stdout=sys.stdout; sys.stdout=open('OUTPUT', 'w')"; cat) \
		| $cmd -
}
test_reset_state_ () {
	test -z "$test_init_done_" && test_init_

	test_subtest_known_broken_=
	test_subtest_missing_external_prereqs_=
}

# called once before the first subtest
test_init_ () {
	test_init_done_=t

	# skip all tests if there were external prerequisites missing during init
	test_check_missing_external_prereqs_ "all tests in $this_test" && test_done
}

# Test the binaries we have just built.  The tests are kept in
# test/ subdirectory and are run in 'trash directory' subdirectory.
TEST_DIRECTORY=$(pwd)

export PATH

# Test repository
test="tmp.$(basename "$0" .sh)"
test -n "$root" && test="$root/$test"
case "$test" in
/*) TMP_DIRECTORY="$test" ;;
 *) TMP_DIRECTORY="$TEST_DIRECTORY/$test" ;;
esac
test ! -z "$debug" || remove_tmp=$TMP_DIRECTORY
rm -fr "$test" || {
	GIT_EXIT_OK=t
	echo >&5 "FATAL: Cannot prepare test area"
	exit 1
}

mkdir -p "${test}"

# load local test library
. ./test-local.sh

# Use -P to resolve symlinks in our working directory so that the cwd
# in subprocesses like git equals our $PWD (for pathname comparisons).
cd -P "$test" || error "Cannot setup test environment"

if test "$verbose" = "t"
then
	exec 4>&2 3>&1
else
	exec 4>test.output 3>&4
fi

this_test=${0##*/}
for skp in $XAPERS_SKIP_TESTS
do
	to_skip=
	for skp in $XAPERS_SKIP_TESTS
	do
		case "$this_test" in
		$skp)
			to_skip=t
		esac
	done
	case "$to_skip" in
	t)
		say_color skip >&3 "skipping test $this_test altogether"
		say_color skip "skip all tests in $this_test"
		test_done
	esac
done

# Provide an implementation of the 'yes' utility
yes () {
	if test $# = 0
	then
		y=y
	else
		y="$*"
	fi

	while echo "$y"
	do
		:
	done
}

# Fix some commands on Windows
case $(uname -s) in
*MINGW*)
	# Windows has its own (incompatible) sort and find
	sort () {
		/usr/bin/sort "$@"
	}
	find () {
		/usr/bin/find "$@"
	}
	sum () {
		md5sum "$@"
	}
	# git sees Windows-style pwd
	pwd () {
		builtin pwd -W
	}
	# no POSIX permissions
	# backslashes in pathspec are converted to '/'
	# exec does not inherit the PID
	;;
*)
	test_set_prereq POSIXPERM
	test_set_prereq BSLASHPSPEC
	test_set_prereq EXECKEEPSPID
	;;
esac

test -z "$NO_PERL" && test_set_prereq PERL
test -z "$NO_PYTHON" && test_set_prereq PYTHON

# test whether the filesystem supports symbolic links
ln -s x y 2>/dev/null && test -h y 2>/dev/null && test_set_prereq SYMLINKS
rm -f y
