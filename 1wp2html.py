#!/usr/bin/python3

# 1wp2html : Converts Atari ST 1stWord+ files to HTML.
# Copyright 2024 Markus Gutschke
#
# Based on 1wp2rtf v1.1
# Copyright 2003, 2016, 2019 Pont Lurcock, email pont@talvi.net
#
# This program is released as free software under the terms of the GNU
# General Public License version 3. Full license text is available
# from http://www.gnu.org/licenses/gpl.html or
# http://www.opensource.org/licenses/gpl-license.php or postally from
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307 USA

import argparse
import html
import re
from copy import deepcopy


class Converter:
    def __init__(self, name, infile, outfile):
        self.name = name
        self.infile = infile
        self.outfile = outfile
        self.this_char = -1
        self.prev_char = -1
        self.follow_char = b''
        self.run_length = 0
        self.has_begun = False
        self.footnote_line = 0

        self.header_template = ['', '', '', False]
        self.footer_template = ['', '', '', False]
        self.page_length = 66
        self.head_tof = 1
        self.head_margin = 3
        self.foot_margin = 3
        self.foot_bof = 5
        self.lines15 = False
        self.ruler = { 'left_margin': 0, 'width': 65,
                       'tab_stops': { (i*5, '\t')  for i in range(65//5) },
                       'pitch': 65, 'justified': True, 'spacing': 1,
                       'proportional': False, 'dots': False }
        self.note_ruler = deepcopy(self.ruler)
        self.note_above = 0
        self.note_below = 0
        self.note_sep_len = 0
        self.note_num_offset = 1

        self.dispatch_table = {
            -1: self.finish,
            8:  self.w_backspace,        # ^H
            9:  self.w_tab,              # ^I
            10: self.linefeed,           # ^J
            11: self.pagebreak_cond,     # ^K
            12: self.w_pagebreak_uncond, # ^L
            24: self.footnoteref,        # ^X
            25: self.w_hyphen,           # ^Y
            27: self.esc_seq,            # ^[
            28: self.w_indent_more,      # ^\
            29: self.w_indent,           # ^]
            30: self.w_space,            # ^^
            31: self.start_format_seq,   # ^_
            32: self.w_space,            # ' '
            127: self.w_delete           # '\x7F'
        }

        self.st2unicode = [ \
            '\x00', '\u21e7', '\u21e9', '\u21e8', '\u21e6', '\U0001fbbd',
            '\U0001fbbe', '\U0001fbbf', '\u2713', '\U0001f552', '\U0001f514',
            '\u266a', '\u240c', '\u240d', ' ', ' ', '\U0001fbf0', '\U0001fbf1',
            '\U0001fbf2', '\U0001fbf3', '\U0001fbf4', '\U0001fbf5',
            '\U0001fbf6', '\U0001fbf7', '\U0001fbf8', '\U0001fbf9', '\u0259',
            '\u241b', '\xad', ' ', ' ', ' ', '\xa0',
                 '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',',
            '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F',
            'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
            'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '{', '|', '}', '~', '\u2302',
            '\xc7', '\xfc', '\xe9', '\xe2', '\xe4', '\xe0', '\xe5', '\xe7',
            '\xea', '\xeb', '\xe8', '\xef', '\xee', '\xec', '\xc4', '\xc5',
            '\xc9', '\xe6', '\xc6', '\xf4', '\xf6', '\xf2', '\xfb', '\xf9',
            '\xff', '\xd6', '\xdc', '\xa2', '\xa3', '\xa5', '\xdf', '\u0192',
            '\xe1', '\xed', '\xf3', '\xfa', '\xf1', '\xd1', '\xaa', '\xba',
            '\xbf', '\u2310', '\xac', '\xbd', '\xbc', '\xa1', '\xab', '\xbb',
            '\xe3', '\xf5', '\xd8', '\xf8', '\u0153', '\u0152', '\xc0', '\xc3',
            '\xd5', '\xa8', '\xb4', '\u2020', '\xb6', '\xa9', '\xae', '\u2122',
            '\u0133', '\u0132', '\u05d0', '\u05d1', '\u05d2', '\u05d3',
            '\u05d4', '\u05d5', '\u05d6', '\u05d7', '\u05d8', '\u05d9',
            '\u05db', '\u05dc', '\u05de', '\u05e0', '\u05e1', '\u05e2',
            '\u05e4', '\u05e6', '\u05e7', '\u05e8', '\u05e9', '\u05ea',
            '\u05df', '\u05da', '\u05dd', '\u05e3', '\u05e5', '\xa7', '\u2227',
            '\u221e', '\u03b1', '\u03b2', '\u0393', '\u03c0', '\u03a3',
            '\u03c3', '\xb5', '\u03c4', '\u03a6', '\u0398', '\u03a9', '\u03b4',
            '\u222e', '\u03d5', '\u20ac', '\u2229', '\u2261', '\xb1', '\u2265',
            '\u2264', '\u2320', '\u2321', '\xf7', '\u2248', '\xb0', '\u2022',
            '\xb7', '\u221a', '\u207f', '\xb2', '\xb3', '\xaf' ]

    def w_char(self, char): pass
    def w_textstyle(self, bold, light, italic, underline,
                    superscript, subscript): pass
    def w_gfx(self, x, y, gfx): pass
    def w_ruler(self, ruler, is_footnote): pass
    def w_backspace(self): pass
    def w_tab(self): self.outfile.write('\t')
    def w_linefeed(self): self.outfile.write('\n')
    def w_pagebreak_cond(self, lines): pass
    def w_pagebreak_uncond(self): pass
    def w_footnoteref(self, lines, n): pass
    def w_begin_footnote(self, n): pass
    def w_end_footnote(self): pass
    def w_hyphen(self): pass
    def w_indent(self): pass
    def w_indent_more(self): pass
    def w_space(self): pass
    def w_delete(self): pass
    def w_begin(self): pass
    def w_finish(self): pass

    def begin(self):
        """First printable character is about to be read. The header has
        been parsed by this time, and global flags, settings and rulers
        are valid."""
        if not self.has_begun:
            self.has_begun = True
            self.w_begin()

    def finish(self):
        """End-of-file has been reached."""
        self.w_finish()

    def linefeed(self):
        self.w_linefeed()
        if self.footnote_line > 0:
            self.footnote_line -= 1
            if self.footnote_line == 0:
                self.w_end_footnote()

    def getchar(self, ignore_cr = True):
        """Get the next character from the input file.
        Ignore CR in CRLF pairs unless told to return it, because it could
        be part of a sequences of binary bytes."""
        if self.follow_char != b'':
            c = self.follow_char
        else:
            c = self.infile.read(1)
        self.follow_char = b''
        if c == b'':
            self.this_char = -1
            return -1
        if c == b'\r':
            c = self.infile.read(1)
            if c != b'\n' or not ignore_cr:
                self.follow_char = c
                c = b'\r'
        self.prev_char = self.this_char
        self.this_char = ord(c)

        if self.this_char == self.prev_char:
            self.run_length += 1
        else:
            self.run_length = 0
        return self.this_char

    def footnoteref(self):
        lines = 0
        while True:
            c = self.getchar()
            if c == 44: # ,
                break
            elif c == -1:
                return
            lines = 10*lines + c - 48
        n = 0
        while True:
            c = self.getchar()
            if c == 24: # ^X
                break
            elif c == -1:
                return
            n = 10*n + c - 48
        self.this_char = 24 # ^X
        self.w_footnoteref(lines, n)

    def pagebreak_cond(self):
        lines = self.getchar(False) - 16
        self.this_char = 11 # ^K
        self.w_pagebreak_cond(lines)

    def esc_seq(self):
        """An escape sequence begins with the character ^] (27). The only
        case we handle is where this is immediately followed by a code
        indicating a change in the character style. In any other case
        we chomp bytes till we hit a 0, indicating the end of the
        escape sequence."""
        c = self.getchar(False)
        if c & 0xc0 == 0x80:
            # c is a bitfield indicating styles we want active
            self.w_textstyle(c & 0x01 > 0, c & 0x02 > 0,
                             c & 0x04 > 0, c & 0x08 > 0,
                             c & 0x10 > 0, c & 0x20 > 0)
        if c == 0xc0:
            # literal escape sequence -- skip it
            c = self.getchar(False)
            while True:
                prev = this
                c = self.getchar(False)
                if (prev == 27 and c == 0) or c == -1:
                    break
        # anything else ignored
        self.this_char = 27 # ^[

    def start_format_seq(self):
        """A format sequence begins with a ^_ (31) and ends with a ^J (10).
        We support a subset of sequences. We can recognize global
        flags '0', the format of the header '1', the format of the
        footer '2', flags for footnote formatting 'F', footnotes 'N',
        embedded graphics '8', and the ruler format '9' or 'R'."""
        c = self.getchar()
        if c == 48: # ^_0
            parms = []
            while True:
                c = self.getchar()
                if c == 10 or c == -1: # \n
                    break
                parms.append(c)
            if len(parms) >= 2:
                self.page_length = (parms[0] - 48)*10 + parms[1] - 48
            if len(parms) >= 4:
                self.head_tof = (parms[2] - 48)*10 + parms[3] - 48
            if len(parms) >= 6:
                self.head_margin = (parms[4] - 48)*10 + parms[5] - 48
            if len(parms) >= 8:
                self.foot_margin = (parms[6] - 48)*10 + parms[7] - 48
            if len(parms) >= 10:
                self.foot_bof = (parms[8] - 48)*10 + parms[9] - 48
            if len(parms) >= 14:
                self.lines15 = parms[13] != '0'
        elif c == 49 or c == 50: # ^_1 and ^_2
            i = 0
            template = self.header_template if c == 49 else self.footer_template
            template[0] = ''
            while True:
                c = self.getchar()
                if c == 10 or c == -1: # \n
                    break
                elif c == 31: # ^_
                    i += 1
                    template.append('' if i <= 2 else False)
                if i > 2:
                    template[i] = c != 48
                    i += 1
                else:
                    template[i] = template[i] + chr(c)
        elif c == 56: # ^_8
            gfx = ''
            while True:
                c = self.getchar()
                if c == -1:
                    return
                if c == 10: # \n
                    break
                gfx += chr(c)
            self.this_char = 31 # ^_
            if len(gfx) < 10: return
            x = int(gfx[0:4])
            y = int(gfx[4:8])
            dirs = int(gfx[8])
            if not 0 <= x <= 9999 or not 0 <= y <= 9999 or not 2 <= dirs <= 9:
                return
            self.w_gfx(x, y, '..\\' * max(0, dirs-1) +
                       ''.join([self.st2unicode[ord(gfx[i])] \
                                for i in range(9, len(gfx)) ]).lstrip('\\'))
        elif c == 57 or c == 82: # ^_9 and ^_R
            ruler = ''
            r = self.ruler if c == 57 else self.note_ruler
            while True:
                c = self.getchar()
                if c == 10 or c == -1: # \n
                    break
                ruler += chr(c)
            r['left_margin'] = ruler.index('[')
            r['width'] = ruler.index(']') + 1 # includes left margin
            r['tab_stops'] = { (i, '\t') if ch == '\a' else ch \
                               for i,ch in enumerate(ruler) if ch in ('\a','#')}
            try:
                r['pitch'] = (65, 78, 112, 39)[ord(ruler[r['width']])-48]
            except:
                r['pitch'] = 65
            try:
                r['justified'] = ruler[r['width'] + 1] != '0'
            except:
                r['justified'] = True
            try:
                r['spacing'] = min(1, max(9, ord(ruler[r['width'] + 2]) - 48))
            except:
                r['spacing'] = 1
            try:
                r['proportional'] = ruler[r['width'] + 3] != '0'
            except:
                r['proportional'] = False
            r['dots'] = ':' in ruler
            self.w_ruler(dict(r), r == self.note_ruler)
        elif c == 69: # ^_E:
            # This sequence should only ever show up at the end of a list of
            # footnotes. We don't normally expect to encounter it in the wild.
            self.this_char = 31 # ^_
            return
        elif c == 70: # ^_F
            parms = []
            while True:
                c = self.getchar()
                if c == 10 or c == -1: # \n
                    break
                parms.append(c)
            if len(parms) >= 3: self.note_above = parms[2] - 48
            if len(parms) >= 4: self.note_below = parms[3] - 48
            if len(parms) >= 8: self.note_sep_len = parms[7] - 48
            if len(parms) >= 11: self.note_num_offset = parms[10] - 48
        elif c == 78: # ^_N
            self.this_char = 31 # ^_
            if self.footnote_line > 0: return
            n = 0
            try:
                while True:
                    c = self.getchar()
                    if c == 10 or c == -1: # \n
                        return
                    if c == 58: # :
                        break
                    n = 10*n + c - 48
                self.this_char = 31 # ^_
                if not 1 <= n <= 999: return
                parms = []
                for i in range(3):
                    k = 0
                    for j in range(4):
                        c = self.getchar()
                        if c == 10 or c == -1: return # \n
                        k = 10*k + c - 48
                    self.this_char = 31 # ^_
                    if not 1 <= k <= 9999: return
                    parms.append(k)
            except:
                self.this_char = 31 # ^_
                return
            self.footnote_line = parms[2]
            self.w_begin_footnote(n)
        while True:
            if c == 10 or c == -1: # \n
                return
            c = self.getchar()
        self.this_char = 31 # ^_

    def convert(self):
        """Performs the actual conversion."""
        skip = 0
        # Skip denotes whether to skip the next read and just use
        # what's in this_char (if a function has read ahead, say)
        while True:
            if not skip:
                self.getchar()
            if self.this_char in self.dispatch_table:
                fnc = self.dispatch_table[self.this_char]
                if fnc != self.start_format_seq:
                    self.begin()
                skip = fnc()
            else:
                self.begin()
                skip = self.w_char(chr(self.this_char))
            if self.this_char == -1:
                break


class DOMConverter(Converter):

    def __init__(self, name, infile, outfile):
        Converter.__init__(self, name, infile, outfile)
        self.dom = []
        self.new_para = True
        self.indents = 0
        self.emptyline = True
        self.active_style = ()

    def w_linefeed(self):
        if self.prev_char != 30 or self.run_length < 2 and self.emptyline:
            self.add_char_to_dom('')
            self.new_para = True
            self.idents = 0
        self.emptyline = True

    def w_char(self, ch):
        self.add_char_to_dom(ch)
        self.emptyline = False
        if self.new_para:
            self.new_para = False
            self.indents = 0

    # 1stWord+ files use four kinds of spaces:
    # * padding after ^] (29) or ^^ (30): ^\ (28)
    # * begin indent: ^] (29)
    # * normal variable-width interword spacing: ^^ (30)
    # * non-breaking hard space: ' ' (32)
    # This is a function of the file format encoding the
    # visual representation in preference over the logical
    # formatting information. Each of these spaces represents
    # an actual space character on screen/paper. The program
    # uses the different types of spaces when deciding how to
    # reformat paragraphs when the user explicitly triggers
    # this operation.

    def w_indent(self):
        indents = 0
        while True:
            # count the number of indent_more ^\ (28) to measure indentation
            c = self.getchar()
            if c != 28: # ^\
                break
            indents += 1
        # If the sequence is terminated by a \n (10), it's an empty line so
        # we ignore it.
        if c != 10 and self.indents == 0:
            self.indents = indents
            self.new_para = False
        if c == 10: # \n
            return 0
        else:
            return 1

    def w_indent_more(self):
        pass

    def w_space(self):
        if self.emptyline and self.this_char == 30 and self.prev_char == 30:
            self.add_char_to_dom(' ')
            self.add_char_to_dom(' ')
            self.emptyline = False
        elif not self.emptyline and \
           self.prev_char not in (10, 28, 29):
            self.add_char_to_dom(' ' if self.this_char == 32 or \
                                 self.this_char == 30 and \
                                 self.prev_char in (28, 29, 30, 32) else '\x1E')
        return

    def w_textstyle(self, bold, light, italic, underline,
                    superscript, subscript):
        style = set()
        if bold: style.add('bold')
        elif light: style.add('light')
        if italic: style.add('italic')
        if underline: style.add('underline')
        if superscript: style.add('superscript')
        elif subscript: style.add('subscript')
        self.add_style_to_dom(tuple(style))

    def w_gfx(self, x, y, gfx):
        pass

    def w_ruler(self, ruler, is_footnote):
        self.dom.append(ruler)

    def w_backspace(self):
        pass

    def w_delete(self):
        pass

    def w_tab(self):
        pass

    def w_pagebreak_cond(self, lines):
        pass

    def w_pagebreak_uncond(self):
        pass

    def w_footnoteref(self, lines, n):
        pass

    def w_begin_footnote(self, n):
        pass

    def w_end_footnote(self):
        pass

    def w_hyphen(self):
        if self.getchar() == 10:
            self.add_char_to_dom('\x1c')
        else:
            self.add_char_to_dom('-')
            return 1

    def w_begin(self):
        pass

    def w_finish(self):
        self.cleanUpDOM()
        # print(repr(self.dom))
        self.domToHTML()

    def add_char_to_dom(self, ch):
        if len(self.dom) == 0 or not isinstance(self.dom[-1], list) or\
           (self.new_para and len(self.dom[-1]) > 0):
            self.new_para = False
            self.dom.append([self.active_style])
        cur_para = self.dom[-1]
        if len(cur_para) == 0 or not isinstance(cur_para[-1], str):
            cur_para.append('')
        if ch:
            cur_para[-1] = cur_para[-1] + self.st2unicode[ord(ch)]

    def add_style_to_dom(self, obj):
        self.active_style = obj
        if len(self.dom) == 0 or not isinstance(self.dom[-1], list):
            if not obj:
                return
            self.dom.append([])
        self.dom[-1].append(obj)

    def cleanUpDOM(self):
        dom = []
        for para in self.dom:
            if isinstance(para, list):
                style = None
                p = []
                for line in para:
                    if isinstance(line, str):
                        if line:
                            if style != None:
                                p.append(style)
                                style = None
                            p.append(line)
                    elif line or p:
                        style = line
                dom.append(p)
            else:
                dom.append(para)
        self.dom = dom

    def domToHTML(self):
        self.outfile.write(
          f'<!DOCTYPE html>\n'
          f'<html>\n'
          f'<head>\n'
          f'<style>\n'
          f'html {{\n'
          f'  font-family: Noto Sans Mono, Courier New, monospace;\n'
          f'}}\n'
          f'p {{\n'
          f'  margin-block: 0 0;\n'
          f'  text-align: justify;\n'
          f'  text-wrap: pretty;\n'
          f'}}\n'
          f'.elite p *, .condensed p *, .expanded p * {{\n'
          f'  vertical-align: top;\n'
          f'}}\n'
          f'.elite sub, .condensed sub, .expanded sub,\n'
          f'.elite sup, .condensed sup, .expanded sup {{\n'
          f'  vertical-align: revert;\n'
          f'}}\n'
          f'.pica p span {{\n' # 65 chars per line
          f'}}\n'
          f'.elite p span {{\n' # 78 chars per line
          f'  display: inline-block;\n'
          f'  font-size: calc(65/78*100%);\n'
          f'  transform: scaleY(calc(78/65));\n'
          f'  transform-origin: 0 0;\n'
          f'}}\n'
          f'.condensed p span {{\n' # 112 chars per line
          f'  display: inline-block;\n'
          f'  font-size: calc(65/112*100%);\n'
          f'  transform: scaleY(calc(112/65));\n'
          f'  transform-origin: 0 0;\n'
          f'}}\n'
          f'.expanded p span {{\n' # 39 chars per line
          f'  display: inline-block;\n'
          f'  font-size: calc(65/39*100%);\n'
          f'  transform: scaleY(calc(39/65));\n'
          f'  transform-origin: 0 0;\n'
          f'}}\n'
          f'</style>\n'
          f'<title>{self.name}</title>\n'
          f'</head>\n'
          f'<body>\n')
        active_div = False
        cur_width = -1
        cur_pitch = -1
        for para in self.dom:
            if isinstance(para, list):
                if not para:
                    self.outfile.write('<br/>\n')
                else:
                    style = '' if self.ruler['justified'] \
                            else ' style="text-align: left"'
                    self.outfile.write(f'<p{style}><span>')
                    tags = ''
                    closing = ''
                    for line in para:
                        if isinstance(line, str):
                            if tags:
                                self.outfile.write(tags)
                                tags = ''
                            self.outfile.write(
                                re.sub(r'([\u05d0-\u05ea])', r'<span>\1</span>',
                                       html.escape(line)))
                        else:
                            if not tags and closing:
                                self.outfile.write(closing)
                                closing = ''
                            tags = ''
                            if 'bold' in line:
                                tags += '<b>'
                                closing = '</b>' + closing
                            if 'light' in line:
                                tags += '<span style="color: #666">'
                                closing  = '</span>' + closing
                            if 'italic' in line:
                                tags += '<em>'
                                closing = '</em>' + closing
                            if 'underline' in line:
                                tags += '<u>'
                                closing = '</u>' + closing
                            if 'superscript' in line:
                                tags += '<sup>'
                                closing = '</sup>' + closing
                            if 'subscript' in line:
                                tags += '<sub>'
                                closing = '</sub>' + closing
                    if not tags and closing:
                        self.outfile.write(closing)
                    self.outfile.write('</span></p>\n')
            else:
                if para['width'] != cur_width or para['pitch'] != cur_pitch:
                    cur_width = para['width']
                    width = cur_width*65.0/para['pitch']
                    cur_pitch = para['pitch']
                    try:
                        pitch = { 65: 'pica', 78: 'elite', 112: 'condensed',
                                  39: 'expanded'
                                }[cur_pitch]
                        cls = f' class="{pitch}"'
                    except:
                        cls = ''
                    if active_div:
                        self.outfile.write('</div>\n')
                    active_div = True
                    self.outfile.write(f'<div style="width: {width}rch;"{cls}>')
        if active_div:
            self.outfile.write('</div>\n')
        self.outfile.write(
          r'<script>''\n'
          r'  for (var sp of document.getElementsByTagName("span")) {''\n'
          r'    sp.style.marginBottom = ''\n'
          r'      (Number(getComputedStyle(sp).transform.split(",")[3])-1)*''\n'
          r'      sp.clientHeight + "px";''\n'
          r'  }''\n'
          r'</script>''\n')
        self.outfile.write(f'</body>\n'
                           f'</html>\n')

def convert(input_filename, output_filename):
    with open(input_filename, 'rb') as infile, \
         open(output_filename, 'w') as outfile:
        name = (input_filename if not input_filename.startswith('/dev') \
                else output_filename).split('/')[-1]
        converter = DOMConverter(name, infile, outfile)
        converter.convert()

def main():
    parser = argparse.ArgumentParser(
        description='Convert Atari ST 1stWord+ files to HTML files.')

    parser.add_argument('-f', '--force', action='store_true',
                        help="attempt conversion even if input file doesn't "
                             'appear to be in 1stWord+ format')
    parser.add_argument('input', help='1stWord+ input file')
    parser.add_argument('output', help='HTML output file')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='latin-1') as infile:
        firstline = infile.readline()
    recognized = False
    while True:
        try:
            if not firstline.startswith('\x1f0'):break
            if not 11 <= int(firstline[2:4]) <= 99: break
            if not  0 <= int(firstline[4:6]) <= 19: break
            if not  0 <= int(firstline[6:8]) <= 19: break
            if not  0 <= int(firstline[8:10]) <= 19: break
            if not  0 <= int(firstline[10:12]) <= 19: break
            if not firstline[15] in ('0','1'): break
            recognized = True
        except:
            pass
        break

    if recognized:
        convert(args.input, args.output)
    else:
        if args.force:
            print("{} doesn't look like a 1stWord+ file.\nConverting anyway "
                  'since --force was specified.'.format(args.input))
            convert(args.input, args.output)
        else:
            print("Skipping {} since it doesn't look like a 1stWord+ file.\n"
                  '(Use --force to override.)'.format(args.input))


if __name__ == '__main__':
    main()
