#!/usr/bin/python

# The MIT License - https://github.com/wilas/vbkick/blob/master/LICENSE

# Example usage:
# echo 'Hello World!' | python convert_2_scancode.py
#
# Note:
# Script work with python 2.6+ and python 3
# When scancode not exist for given char
# then script exit with code 1 and an error is write to stderr.
#
# Helpful links - scancodes:
# - basic: http://humbledown.org/files/scancodes.l (http://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html)
# - make and break codes (c+0x80): http://www.win.tue.nl/~aeb/linux/kbd/scancodes-10.html
# - make and break codes table: http://stanislavs.org/helppc/make_codes.html
# - https://github.com/jedi4ever/veewee/blob/master/lib/veewee/provider/core/helper/scancode.rb
#
# Some portions of this file [software code] are provided under the MIT License as specified above, but with "Chris Niswander" as the original licensor for those portions.

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import re

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
    # Builds a dict of multi-character codes 
    # *without* the enclosing angle brackets.
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
         # ^ otherwise < would be impossible in some contexts. :-)
    scancodes['PressAlt'] = '38'    # Depress Left Alt.
    scancodes['RelAlt'] = 'b8'      # Release Left Alt.
    # F1..F10
    for idx in range(1,10):
        scancodes['F%s' % idx] = '%02x' % (idx + 0x3a)
    # VT1..VT12 (Switch to Virtual Terminal)
    for idx in range(1,12):
        # LeftAlt + RightCtrl + F1-12
        scancodes['VT%s' % idx] = '38 e0 1d %02x b8 e0 9d %02x' % (idx + 0x3a, idx +0xba)
    return scancodes

def get_multi_char_codes():
    # Builds a dict of multi-character codes 
    # *with* the enclosing angle brackets.
    scancodes = {}
    for k, v in get_naked_multi_char_codes().items():
      scancodes['<%s>' % k] = v
    return scancodes

def process_multiply(input):
    # process <Multiply(what,times)>
    # example usage: <Multiply(<Wait>,4)> --> <Wait><Wait><Wait><Wait>
    # key thing about multiply_regexpr: match is non-greedy
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
    # The press and release scancodes for each meta key 
    # that is supported as a general meta key.
    keycodes = {}
    for s in ['Ctrl 1d 9d',
              'Shift 2a aa',  # I think left shift.
              'Alt 38 b8',    # Left Alt.
              ('RAlt', 'E0 38', 'E0 B8'),
              ('RCtrl', 'E0 1D', 'E0 9D'),
              ('Win', 'e0 5b', 'e0 db'),    # Left Windows key.
              ('RWin', 'E0 5C', 'E0 DC'),  # Right Windows key.
              ##('ATRtWin', 'E0 27', 'E0 F0 27'),
             ]:
      if isinstance(s, tuple):
         k, press, release = s
      else:
         k, press, release = s.split()  # Three little words. :-)
      keycodes[k] = press, release
    return keycodes

def de_duplicate(mylist, omit_false=True):
    # Given a list /mylist/, returns a list with the duplicates omitted.
    # If omit_false, also omits any item x such that bool(x) == False.
    # List order is preserved.
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
    # for constructing the metakey combination regular expression.
    return 'meta' + str(i)

def create_meta_regex():
    # Returns a string specifying our regular expression to match
    # a 'meta expression' that specifies a keypress combination
    # including 1 or more meta keys.
    #   'meta expression' examples: '<AltTab>', '<CtrlAltDelete>'

    def escape_key(x):
      # Return x, 
      # escaped if that is necessary to put it in a re character class.
      if x in '<>-[]\\?*+,()':
        return '\\' + x
      return x

    def named_meta_group(group_name):
      # Returns a *named* regular expression 
      # that matches any meta key's name.
      return  (   '(?P<' + group_name + '>' 
                + '|'.join([('(%s)' % x) for x in metakey_code_keys])
                + ')'
              )

    def named_meta_groups(count):
      # Returns a regular expression that matches 1 to /count/
      # metakey names.  
      # Each meta group is named using name_of_ith_meta_group().
      groups = [named_meta_group(name_of_ith_meta_group(0))]
        # ^ first meta group is mandatory.
      for i in range(1, count):
        groups.append(named_meta_group(name_of_ith_meta_group(i)) 
                      + '?'  # each additional meta_group is optional.
                     )
        # additional meta groups are optional.
      return ''.join([group 
                      ##+ '\\s*' 
                      ##  # should permit optional space character(s)
                      ##  #   after each meta_group, for readability of expr
                      ##  # but doesn't actually work.
                      ##  # (A poem on how software isn't all that great.)
                      for group in groups])

    metakey_codes = get_metakey_codes()
    metakey_code_keys = list(metakey_codes.keys())
    metakey_code_keys.sort(reverse=True)
      # ^ longer strings before their beginnings,
      #   e.g. 'Shift' before 'Sh'

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
                + '(?P<normal>%s)?' % 
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
    # Recognizes sequences of the form '<NUMBER>', 
    # where NUMBER is at least 3 decimal digits,
    # and translates them into pseudocodes of the form 'sleep:NUMBER'.
    # These pseudocodes are NOT understood by VBoxManage utility.
    # However, user-written code that uses the results 
    # of convert_2_scancode translation may recognize these pseudocodes.
    # (At present, these pseudocodes are used by the stringtyper.py
    #  utility)
    #
    # The minimum of 3 decimal digits is imposed 
    # to allow for possible future feature '<SCANCODE_IN_HEXADECIMAL>',
    #   e.g. '<23>' as the literal scancode hexadecimal 23.

    if keys_array == False:
        # Just to support cheesy tests.
        keys_array = [-1 for c in input]

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
    

def translate_meta(input, keys_array=False):
    # Works like translate_chars(), 
    #   to do part of the work of translate_chars().  Specifically:
    # Finds and translates meta-key expressions
    #   such as <AltTab>, <Ctrlt>, <ShiftCtrlt>, <AltSpacebar>, etc.
    # As a sneaky extra, handles meta-only press-release cases 
    #   such as <Win>.  
    #   (This is significant because 
    #      e.g. "<Win>t" can differ in intended effect from "<Wint>".)
    #
    # CAVEAT: 
    #   There is a limit on how many meta keys you can have 
    #     in a single meta key press expression.
    #     The limit is MetaKeysInMetaExpression_Max.
    #     Why, you may ask?
    #     The standard library re module does *not* so easily provide 
    #     ordered list of *all* matches 
    #     for a named group in a regular expression.  Therefore,
    #     instead of using a single group with + suffix for all meta keys,
    #     we use each meta key matching group to match one meta key name
    #     within the meta expression.
    #     This permits us to find and press meta keys in the same order
    #     as they occur in the meta keypress expression.
    #   If I didn't care about preserving this order,
    #     the code could be simpler and avoid this limit.
    #   It would surely be possible for me to kludge around 
    #     to transcend this limit, but the code would probably become
    #     substantially more complicated.
    # 
    # POSSIBLE FUTURE CHANGE IDEA:
    #   This code (and the regular expression) could be changed
    #   to handle non-meta bracketed expressions as a simple case:
    #   meta expressions happening to have zero meta keys.
    #   However, preserving the older code probably helps to illustrate
    #   how convert_2_scancode.py actually works internally
    #   when a human is (re)learning this module's inner workings.
    #   

    if keys_array == False:
        # Just relevant for cheesy unit tests.
        keys_array = [-1 for c in input]

    def elective_noise():
      # When debugging, can be made to print useful debugging info.
      if 0:
        pass
        print ('keys_array:', keys_array)

    metakey_codes = get_metakey_codes()
    onechar_scancodes = get_one_char_codes()
    naked_spc_scancodes = get_naked_multi_char_codes()

    def components_to_scancodes_str(components):
        # Given a list of meta-key keypress components, 
        # possibly ending in a non-meta key such as 'Return' or 't',
        # returns the corresponding scancodes.
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
                # We have leftover components after reaching 
                # what should be the final component 
                # that the other meta keys modify.
                raise Exception("Bad metakey press instruction.  %s" %
                             ' '.join(components))
        # We could do a special case or two here e.g. <CtrlPress>...
        return ' '.join(pre + center + post)

    for match in re.finditer(create_meta_regex(), input):
        s = match.start()
        e = match.end()
        
        match_groups_deduped = de_duplicate(match.groups())

        if len(match.groups()) >= 100:
          raise Exception(
                  "Some implementations of python re"
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
    # Given a string, returns a string of 
    #   corresponding, space-separated scancodes in hexadecimal format
    #   as the VMBoxManage utility likes.
    # Special cases:
    # - "<KEYNAME>" e.g. "<Tab>" is interepreted as typing Tab character.
    # - Meta key expressions, e.g. 
    #     "<Ctrln>" -> Depress Ctrl key, type n, release Ctrl key.
    #     "<CtrlShiftn>" -> Ctrl + Shift + n (analagous to <Ctrln>)
    #     "<AltTab>" -> Alt + Tab 
    #     "<Win>" -> depress and release Win key.
    # - "<NUMBER>" for NUMBER of 3 or more digits
    #     produces a pseudo-scancode "sleep:NUMBER"
    #     which means to sleep for NUMBER milliseconds.
    #     This makes sense only to callers written to understand it.
    #     Only enabled if support_millisecond_expressions is true.


    # Create list to collect information about input string structure.
    # keys_array[i] describes what we have figured out so far
    #   about the meaning of the character input[i].
    # -1 means no key yet assigned to cell in array.
    # keys_array[i] can be multiple scancodes derived from a sequence
    #   of characters starting at input[i].
    #   e.g. input[i]=='n' --> keys_array[i]='10 90'
    #               (the scancodes for depress n key, release n key.)
    # keys_array[i] can be empty string ''
    #   iff we've figured out the significance of input[i]
    #       and that input[i] causes no scancode by itself.
    keys_array = [-1] * len(input)

    def elective_noise():
        # Just relevant for cheesy test/debug.
        if 0:
            pass
            print ('keys_array:', keys_array)

    if support_millisecond_expressions:
        translate_sleeps(input, keys_array)

    translate_meta(input, keys_array)

    # process multi-char codes/marks (special)
    spc_scancodes = get_multi_char_codes()
    for spc in spc_scancodes:
        # find all spc code in input string and mark correspondence cells in keys_array
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

    # remove empty string from keys_array
    keys_array = [x for x in keys_array if x != '']
    elective_noise()
    return keys_array


if __name__ == "__main__":
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
