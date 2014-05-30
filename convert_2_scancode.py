#!/usr/bin/python

"""The MIT License - https://github.com/wilas/vbkick/blob/master/LICENSE

Example usage:
echo 'Hello World!' | python convert_2_scancode.py

Note:
Script works with python 2.6+ and python 3
When scancode doesn't exist for given char
then script exit with code 1 and an error is written to stderr.

Helpful links - scancodes:
- basic: http://humbledown.org/files/scancodes.l (http://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html)
- make and break codes (c+0x80): http://www.win.tue.nl/~aeb/linux/kbd/scancodes-10.html
- make and break codes table: http://stanislavs.org/helppc/make_codes.html
- https://github.com/jedi4ever/veewee/blob/master/lib/veewee/provider/core/helper/scancode.rb

Some portions of this file are provided under the BSD License (2-Clause), with "Chris Niswander" as the original licensor for those portions.  That license is as follows:

Copyright (c) 2014, Chris Niswander
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import sys, re

DEBUG = 0

# How many metakeys can be in a metakey expression?
# e.g. '<ShiftAltCtrl5>' has three metakeys.
MetaKeysInMetaExpression_Max = 4

def _make_scancodes(key_map, str_pattern):
    scancodes = {}
    for keys in key_map:
        offset = key_map[keys]
        for idx, k in enumerate(list(keys)):
            scancodes[k] = str_pattern % (idx + offset, idx + offset + 0x80)
    return scancodes

def get_one_char_codes():
    key_map = {'1234567890-=' : 0x02,
        'qwertyuiop[]' : 0x10,
        'asdfghjkl;\'`' : 0x1e,
        '\\zxcvbnm,./' : 0x2b
    }
    scancodes = _make_scancodes(key_map, '%02x %02x')
    # Shift keys
    key_map = { '!@#$%^&*()_+' : 0x02,
        'QWERTYUIOP{}' : 0x10,
        'ASDFGHJKL:"~' : 0x1e,
        '|ZXCVBNM<>?' : 0x2b
    }
    scancodes.update(_make_scancodes(key_map, '2a %02x %02x aa'))
    return scancodes

def get_naked_multi_char_codes():
    """Builds a dict of multi-character codes 
    *without* the enclosing angle brackets.
    """
    scancodes = {}
    scancodes['Enter'] = '1c 9c'
    scancodes['Backspace'] = '0e 8e'
    scancodes['Spacebar'] = '39 b9'
    scancodes['Return'] = '1c 9c'
    scancodes['Esc'] = '01 81'
    scancodes['Tab'] = '0f 8f'
    scancodes['KillX'] = '1d 38 0e b8'
    scancodes['Wait'] = 'wait'
    scancodes['Up'] = '48 c8'
    scancodes['Down'] = '50 d0'
    scancodes['PageUp'] = '49 c9'
    scancodes['PageDown'] = '51 d1'
    scancodes['End'] = '4f cf'
    scancodes['Insert'] = '52 d2'
    scancodes['Delete'] = '53 d3'
    scancodes['Left'] = '4b cb'
    scancodes['Right'] = '4d cd'
    scancodes['Home'] = '47 c7'
    scancodes['Lt'] = '2a 33 b3 aa'  
         # ^ otherwise < would be difficult in some contexts. :-)
    scancodes['PressAlt'] = '38'    # Depress Left Alt.
    scancodes['RelAlt'] = 'b8'      # Release Left Alt.
    # F1..F10
    for idx in range(1,10):
        scancodes['F%s' % idx] = '%02x' % (idx + 0x3a)
    # VT1..VT12 (Switch to Virtual Terminal)
    for idx in range(1,12):
        """LeftAlt + RightCtrl + F1-12
        """
        scancodes['VT%s' % idx] = '38 e0 1d %02x b8 e0 9d %02x' % (idx + 0x3a, idx +0xba)
    return scancodes

def get_multi_char_codes():
    """Builds a dict of multi-character codes 
    *with* the enclosing angle brackets.
    """
    scancodes = {}
    for k, v in get_naked_multi_char_codes().items():
        scancodes['<%s>' % k] = v
    return scancodes

def process_multiply(input):
    """process <Multiply(what,times)>
    example usage: <Multiply(<Wait>,4)> --> <Wait><Wait><Wait><Wait>
    key thing about multiply_regexpr: match is non-greedy
    """
    multiply_regexpr = '<Multiply\((.+?),[ ]*([\d]+)[ ]*\)>'
    for match in re.finditer(r'%s' % multiply_regexpr, input):
        what = match.group(1)
        times = int(match.group(2))
        # repeating a string given number of times
        replacement = what * times
        # replace Multiply(what,times)> with already created replacement
        input = input.replace(match.group(0), replacement)
    return input

def get_metakey_codes():
    """The press and release scancodes for each meta key 
    that is supported as a general meta key.
    """
    keycodes = {}
    for keyname, press, release in [
              ('Ctrl', '1d', '9d'),   
              ('Shift', '2a', 'aa'),       # I think left shift.
              ('Alt', '38', 'b8'),         # Left Alt.
              ('RAlt', 'E0 38', 'E0 B8'),  # Right Alt.
              ('RCtrl', 'E0 1D', 'E0 9D'),
              ('Win', 'e0 5b', 'e0 db'),   # Left Windows key.
              ('RWin', 'E0 5C', 'E0 DC'),  # Right Windows key.
             ]:
        keycodes[keyname] = press, release
    return keycodes

def de_duplicate(mylist, omit_false=True):
    """Given a list /mylist/, returns a list with the duplicates omitted.
    If omit_false, also omits any item x such that bool(x) == False.
    List order is preserved.
    """
    output = []
    found = set()
    for x in mylist:
        if omit_false and (not x):
            continue
        if x in found:
            continue
        found.add(x)
        output.append(x)
    return output

def name_of_ith_meta_group(i):
    """for constructing the metakey combination regular expression.
    """
    return 'meta' + str(i)

def create_meta_regex():
    """Returns a string specifying our regular expression to match
    a 'meta expression' that specifies a keypress combination
    including 1 or more meta keys.
      'meta expression' examples: '<AltTab>', '<CtrlAltDelete>', '<Ctrlc>'
    """

    def escape_key(x):
        """Return x, 
        escaped if that is necessary to put it in a re character class.
        """
        if x in '<>-[]\?*+,()':
            return '\\' + x
        return x

    def named_meta_group(group_name):
        """Returns a *named* regular expression 
        that matches any meta key's name.
        """
        metakey_re = '|'.join([('(%s)' % x) for x in metakey_code_keys]) 
        return '(?P<%s>%s)' % (group_name, metakey_re)

    def named_meta_groups(count):
        """Returns a regular expression that matches 1 to /count/
        metakey names.  
        Each meta group is named using name_of_ith_meta_group().
        """

        # first meta group is mandatory.
        groups = [named_meta_group(name_of_ith_meta_group(0))]
          
        # additional meta groups are optional.
        for i in range(1, count):
            groups.append(named_meta_group(name_of_ith_meta_group(i)) 
                          + '?'  # each additional meta_group is optional.
                         )
        return ''.join([group for group in groups])

    metakey_codes = get_metakey_codes()
    metakey_code_keys = list(metakey_codes.keys())
    metakey_code_keys.sort(reverse=True)
      # ^ place longer strings before their beginnings,
      #     e.g. 'Shift' before 'Sh'
      #     So we can add alternate names (short vs. long) for keys.

    onechar_scancodes = get_one_char_codes()
    onechar_scancode_keys_escaped = [
           escape_key(x) for x in onechar_scancodes.keys()]

    naked_spc_scancodes = get_naked_multi_char_codes()
    naked_spc_scancodes_keys = list(naked_spc_scancodes.keys())
    naked_spc_scancodes_keys.sort(reverse=True) 
      # ^ longer strings before their beginnings,
      #   e.g. 'Spacebar' before 'Sp'

    all_non_meta_scancode_keys = (
           list(onechar_scancodes.keys()) 
         + list(naked_spc_scancodes.keys()) 
        )
    all_non_meta_scancode_keys_escaped = [
           escape_key(x) for x in all_non_meta_scancode_keys]
    pattern = (   r'\<' 
                + named_meta_groups(MetaKeysInMetaExpression_Max)
                + '(?P<normal>%s)?' %   # optional non-meta key.
                  (
                     '|'.join(  ['(%s)' % x 
                                 for x in naked_spc_scancodes_keys 
                                ]
                                # Some implementations of re 
                                # don't like >100 groups.  
                                # So we shove single characters 
                                # into one set of characters.
                              + ["[%s]" % 
                                 ''.join(onechar_scancode_keys_escaped) 
                                ]
                             )
                  )

                + r'\>'
              )
    return pattern

def translate_sleeps(input, keys_array=False):
    """Recognizes sequences of the form '<NUMBER>', 
    where NUMBER is at least 3 decimal digits,
    and translates them into pseudocodes of the form 'sleep:NUMBER'.
    These pseudocodes are NOT understood by VBoxManage utility.
    However, user-written code that uses the results 
    of convert_2_scancode translation may recognize these pseudocodes.
    (At present, these pseudocodes are used by the stringtyper.py
     utility, which is not part of vbkick.)
    
    The minimum of 3 decimal digits is imposed 
    to allow for possible future feature '<SCANCODE_IN_HEXADECIMAL>',
      e.g. '<23>' as the literal scancode hexadecimal 23.
    If you want less than 100 milliseconds, just use leading zero(s),
      e.g. '<050>' for a 50 millisecond sleep.
    """

    keys_array = ensure_keys_array(input, keys_array)

    for match in re.finditer(r'\<(?P<number>\d{3,})\>', input):
        s = match.start()
        e = match.end()
        
        number_found = match.group('number')
        if number_found:
            keys_array[s] = 'sleep:%s' % number_found

            # mark rest pos given match as empty string in keys_array
            for i in range(s+1, e):
                 keys_array[i] = ''
    return keys_array

def ensure_keys_array(input, keys_array=False):
    """Make sure we have list to collect information 
    about input string structure.

    keys_array[i] describes what we have figured out so far
      about the meaning of the character input[i].
    -1 means no key yet assigned to cell in array.
    keys_array[i] can be multiple scancodes derived from a sequence
      of characters starting at input[i].
      e.g. input[i]=='n' --> keys_array[i]='10 90'
                  (the scancodes for depress n key, release n key.)
    keys_array[i] can be empty string ''
      iff we've figured out the significance of input[i]
          and that input[i] causes no scancode by itself.

    Iff (if and only if)
      input parameter /keys_array/ is not specifically False,
       we assume that it's ok to just return that input parameter's value.
    """
    if keys_array == False:
      return [-1] * len(input)
    return keys_array  # 
    

def translate_meta(input, keys_array=False):
    """Works like translate_chars(), 
      to do part of the work of translate_chars().  Specifically:
    Finds and translates meta-key expressions
      such as <AltTab>, <Ctrlt>, <ShiftCtrlt>, <AltSpacebar>, etc.
    As a sneaky extra, handles meta-only press-release cases 
      such as <Win>.  
      (This is significant because 
         e.g. "<Win>t" can differ in intended effect from "<Wint>".)
    
    CAVEAT: 
      There is a limit on how many meta keys you can have 
        in a single meta key press expression.
        The limit is MetaKeysInMetaExpression_Max.
        Why, you may ask?
        The standard library re module does *not* so easily provide 
        ordered list of *all* matches 
        for a named group in a regular expression.  Therefore,
        instead of using a single group with + suffix for all meta keys,
        we use each meta key matching group to match one meta key name
        within the meta expression.
        This permits us to find and press meta keys in the same order
        as they occur in the meta keypress expression.
      If I didn't care about preserving this order,
        the code could be simpler and avoid this limit.
      It would surely be possible for me to kludge around 
        to transcend this limit, but the code would probably become
        substantially more complicated.
    
    POSSIBLE FUTURE CHANGE IDEA:
      This code (and the regular expression) could be changed
      to handle non-meta bracketed expressions as a simple case:
      meta expressions happening to have zero meta keys.
      However, preserving the older code probably helps to illustrate
      how convert_2_scancode.py actually works internally
      when a human is (re)learning this module's inner workings.
      
    """

    keys_array = ensure_keys_array(input, keys_array)

    def elective_noise(force_output=False):
        """When debugging, can be made to print useful debugging info.
        """
        if DEBUG or force_output:
            print ('keys_array:', keys_array)

    metakey_codes = get_metakey_codes()
    onechar_scancodes = get_one_char_codes()
    naked_spc_scancodes = get_naked_multi_char_codes()

    def components_to_scancodes_str(components):
        """Given a list of meta-key keypress components, 
        such as 'Ctrl', 'Shift', etc...
        possibly ending in a non-meta key such as 'Return' or 't',
        returns the corresponding scancodes.
        e.g. 
           ['t'] --> "14 94"
           ['Ctrl', 'Shift' 't'] --> "1d 2a 14 94 aa 9d"
        """
        pre, post, center = [], [], []
        for i, x in enumerate(components):
            if metakey_codes.get(x, False):
                 press, release = metakey_codes[x]
                 pre.append(press)
                 post.insert(0, release)
            elif naked_spc_scancodes.get(x, False):
                 center = [naked_spc_scancodes[x]]
            elif onechar_scancodes.get(x, False):
                 center = [onechar_scancodes[x]]
            if center and (i+1 < len(components)):
                # Execution has not normally been able to reach this,
                # because normally a sequence of the form <...>
                # that doesn't form a valid meta expression
                # would not be interpreted by translate_meta().
                # So if the code gets to this point,
                # it indicates a bug in the code itself, 
                # which should be exceptional.
                # 
                # We have leftover components after reaching 
                # what should be the final component 
                # that the other meta keys modify.
                raise Exception(
                    "Bad metakey press instruction, or software bug: %s" %
                    ' '.join(components)
                )
        return ' '.join(pre + center + post)

    for match in re.finditer(create_meta_regex(), input):
        s = match.start()
        e = match.end()
        
        match_groups_deduped = de_duplicate(match.groups())

        if len(match.groups()) >= 100:
            # Someone changed the source code 
            # in a way that some Python interpretations won't support!
            raise Exception(
                  "Software bug!  Some implementations of python re"
                  " (regular expressions)"
                  " library don't support more than 100 groups.")

        # just for cheesy debugging/test.
        if 0:
            print (match.groups(), len(match.groups()))
            print (s, e, match_groups_deduped)
            print (match.group('meta0'), match.group('meta1'), 
                   match.group('meta2'), match.group('meta3'), 
                   match.group('normal'))

        keys_array[s] = \
           components_to_scancodes_str(match_groups_deduped)
        # mark rest pos given match as empty string in keys_array
        for i in range(s+1, e):
            keys_array[i] = ''
    return keys_array 

def translate_chars(input, support_millisecond_expressions=False):
    """Given a string, returns a string of 
      corresponding, space-separated scancodes in hexadecimal format
      as the VMBoxManage utility likes.
    Special cases:
    - "<KEYNAME>" e.g. "<Tab>" is interepreted as typing Tab character.
    - Meta key expressions, e.g. 
        "<Ctrln>" -> Depress Ctrl key, type n, release Ctrl key.
        "<CtrlShiftn>" -> Ctrl + Shift + n (analagous to <Ctrln>)
        "<AltTab>" -> Alt + Tab 
        "<Win>" -> depress and release Win key.
    - "<NUMBER>" for NUMBER of 3 or more digits
        produces a pseudo-scancode "sleep:NUMBER"
        which means to sleep for NUMBER milliseconds.
        This makes sense only to callers written to understand it.
        Only enabled if support_millisecond_expressions is true.
    """

    # see definition of ensure_keys_array()
    keys_array = ensure_keys_array(input)

    def elective_noise(force_output=False):
        """When debugging, can be made to print useful debugging info.
        """
        if DEBUG or force_output:
            print ('keys_array:', keys_array)

    if support_millisecond_expressions:
        translate_sleeps(input, keys_array)

    translate_meta(input, keys_array)

    # process multi-char codes/marks (special)
    spc_scancodes = get_multi_char_codes()
    for spc in spc_scancodes:
        # find all spc code in input string 
        # and mark correspondence cells in keys_array
        for match in re.finditer(spc, input):
            s = match.start()
            e = match.end()
            # mark start pos given match as scancode in keys_array
            keys_array[s] = spc_scancodes[spc]
            # mark rest pos given match as empty string in keys_array
            for i in range(s+1, e):
                keys_array[i] = ''
            elective_noise()

    # process single-char codes
    scancodes = get_one_char_codes()
    # convert input string to list
    input = list(input)
    # check only not assign yet (with value equal -1) cells in keys_array
    for index, _ in enumerate(keys_array):
        if keys_array[index] != -1:
            continue
        try:
            keys_array[index] = scancodes[input[index]]
        except KeyError:
            sys.stderr.write('Error: Unknown symbol found - %s\n' % repr(input[index]))
            sys.exit(1)
        elective_noise()

    # remove any empty strings from keys_array
    keys_array = [x for x in keys_array if x != '']
    elective_noise()
    return keys_array

def test_translate_chars_basic():
    """Tests translate_chars() 
    with argument support_millisecond_expressions=False. 
    """
    test_data = [
      ('<Win>', ['e0 5b e0 db']),
      ('<Esc>', ['01 81']),
      ('123', ['02 82', '03 83', '04 84']),
      ('<Win><Wait>gedit<333><Enter>', 
        ['e0 5b e0 db', 'wait', '22 a2', '12 92', '20 a0', 
         '17 97', '14 94', '2a 33 b3 aa', '04 84', '04 84', '04 84', 
         '2a 34 b4 aa', '1c 9c']),
      ('<Ctrln>', ['1d 31 b1 9d']),
      ('<CtrlShiftn>', ['1d 2a 31 b1 aa 9d']),
      ('<CtrlShiftt>', ['1d 2a 14 94 aa 9d']),
      ('ls', ['26 a6', '1f 9f']),
      ('<Enter>', ['1c 9c']),
      ('', []),
      ('<Lt>', ['2a 33 b3 aa']),
      ('<Lt>Ctrln>', 
        ['2a 33 b3 aa', '2a 2e ae aa', '14 94', '13 93', '26 a6', 
         '31 b1', '2a 34 b4 aa']),
      ('<Spacebar>', ['39 b9']),
    ]

    failed_tests = []
    for input_, scancodes in test_data:
        translated = translate_chars(
            input_, support_millisecond_expressions=False)
        if translated != scancodes:
             failed_tests.append([input_, translated])
    if failed_tests:
        raise Exception(
                 "translate_chars_basic()"
                 " gave bad results: %s" % repr(failed_tests)
        )

def test_translate_chars_with_millisecond_expressions():
    """Tests translate_chars() with support_millisecond_expressions=True. 
    """
    test_data_with_millisecond_expressions = [
      ('<Win>', ['e0 5b e0 db']),
      ('<Esc>', ['01 81']),
      ('123', ['02 82', '03 83', '04 84']),
      ('<Win><Wait>gedit<333><Enter>', 
        ['e0 5b e0 db', 'wait', '22 a2', '12 92', '20 a0', 
         '17 97', '14 94', 'sleep:333', '1c 9c']),
      ('123', ['02 82', '03 83', '04 84']),
      ('<Ctrln>', ['1d 31 b1 9d']),
      ('<CtrlShiftn>', ['1d 2a 31 b1 aa 9d']),
      ('<Win><333>terminal<2000><Enter>', 
        ['e0 5b e0 db', 'sleep:333', '14 94', '12 92', '13 93', 
         '32 b2', '17 97', '31 b1', '1e 9e', '26 a6', 
         'sleep:2000', '1c 9c']),
      ('<CtrlShiftt>', ['1d 2a 14 94 aa 9d']),
      ('ls', ['26 a6', '1f 9f']),
      ('<Enter>', ['1c 9c']),
      ('', []),
      ('<Lt>', ['2a 33 b3 aa']),
      ('<Lt>Ctrln>', 
        ['2a 33 b3 aa', '2a 2e ae aa', '14 94', '13 93', '26 a6', 
         '31 b1', '2a 34 b4 aa']),
      ('<Spacebar>', ['39 b9']),
    ]

    failed_tests = []
    for input_, scancodes in test_data_with_millisecond_expressions:
        translated = translate_chars(
            input_, support_millisecond_expressions=True)
        if translated != scancodes:
             failed_tests.append([input_, translated])
    if failed_tests:
        raise Exception(
                 "translate_chars() with millisecond expressions"
                 " gave bad results: %s" % repr(failed_tests)
        )


def self_test():
    """Tests translate_chars(). 
    To test most of this module's functionality in a version of Python,
    you can start up the appropriate python interpreter,
    import this module, and run this function.
    """
    test_translate_chars_basic()
    test_translate_chars_with_millisecond_expressions()

if __name__ == "__main__":
    self_test()  # cheap at twice the price.
    # read from stdin
    input = sys.stdin.readlines()
    # convert input list to string
    input = ''.join(input).rstrip('\n')
    # process multiply
    input = process_multiply(input)
    # replace white-spaces with <Spacebar>
    input = input.replace(' ', '<Spacebar>')
    # process keys
    keys_array = translate_chars(input)
    # write result to stdout
    print(' '.join(keys_array))

#  As per: http://vimdoc.sourceforge.net/htmldoc/options.html#'tabstop'
# Set 'tabstop' and 'shiftwidth' to whatever you prefer and use 'expandtab'.
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

