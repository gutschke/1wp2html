#!/usr/bin/python3

# 1wp2rtf : Converts Acorn 1stWord+ files to RTF.
# Copyright 2003, 2016, 2019 Pont Lurcock, email pont@talvi.net
#
# version 1.1
#
# Handles normal text, block indentation, bold, underline, italic,
# superscript, and subscript. Tweaked to handle the files I needed to
# convert, and to import nicely into Linux OpenOffice.org v1.1.0 --
# YMMV.
#
# This program is released as free software under the terms of the GNU
# General Public License version 3. Full license text is available
# from http://www.gnu.org/licenses/gpl.html or
# http://www.opensource.org/licenses/gpl-license.php or postally from
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307 USA

import string
import sys


class Converter:
    """Converts 1wp to a plain text file."""

    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self.this_char = -1
        self.prev_char = -1
        self.run_length = 0

        self.dispatch_table = {
            -1: self.finish,
            8:  self.w_backspace,
            9:  self.w_tab,
            10: self.w_linefeed,
            11: self.pagebreak_cond,
            12: self.w_pagebreak_uncond,
            13: self.w_return,
            24: self.footnoteref,
            25: self.w_hyphen,
            27: self.esc_seq,
            28: self.w_indent_more,
            29: self.w_indent,
            30: self.w_space,
            31: self.start_format_seq,
            32: self.w_space,
            127: self.w_delete
            }

    def w_char(self, char):
        # any character that's not handled by one of the other functions.
        self.outfile.write(char)

    def w_textstyle(self, bold, light, italic, underline,
                    superscript, subscript):
        """change the character text style"""
        pass

    def w_backspace(self):
        pass

    def w_tab(self):
        self.outfile.write("\x09")
        pass

    def w_linefeed(self):
        self.outfile.write("\n")
        pass

    def w_pagebreak_cond(self, lines):
        """conditional page break"""
        pass

    def w_pagebreak_uncond(self):
        """unconditional page break"""
        pass

    def w_return(self):
        self.outfile.write("\n")

    def w_footnoteref(self, n):
        self.outfile.write("[" + str(n) + "]")

    def w_hyphen(self):
        """soft hyphen"""
        pass

    # As far as I can tell, 1stWord+ files use three kinds of spaces:
    # * normal interword spacing: 30
    # * begin indent (first character on a line): 29
    # * indent (you get a sequence of these after a 29): 28
    # I've also very occasionally seen a normal ASCII space (32),
    # which is treated here in the same way as a 30.

    def w_indent(self):
        self.outfile.write(" ")
        pass

    def w_indent_more(self):
        self.outfile.write(" ")
        pass

    def w_space(self):
        self.outfile.write(" ")
        pass

    def w_delete(self):
        pass

    def finish(self):
        """Called when the end of a file is reached."""
        pass

    def getchar(self):
        """get the next character from the input file"""
        c = self.infile.read(1)
        if c == b"":
            self.this_char = -1
            return -1
        self.prev_char = self.this_char
        self.this_char = ord(c)

        if self.this_char == self.prev_char:
            self.run_length += 1
        else:
            self.run_length = 0
        return self.this_char

    def footnoteref(self):
        self.infile.read(2)  # skip meaningless x and y values
        n = self.getchar()
        self.w_footnoteref(n)

    def pagebreak_cond(self):
        lines = self.getchar()
        self.w_pagebreak_cond(lines)

    def esc_seq(self):
        """An escape sequence begins with the character 27. The only
        case we handle is where this is immediately followed by a code
        indicating a change in the character style. In any other case
        we chomp bytes till we hit a 0, indicating the end of the
        escape sequence."""

        c = self.getchar()
        if c & 0xc0 == 0x80:
            # c is a bitfield indicating styles we want active
            self.w_textstyle(c & 0x01 > 0, c & 0x02 > 0,
                             c & 0x04 > 0, c & 0x08 > 0,
                             c & 0x10 > 0, c & 0x20 > 0)
        if c == 0xc0:
            # literal escape sequence -- skip it
            this = self.getchar()
            while True:
                prev = this
                this = self.getchar()
                if prev == 27 and this == 0:
                    break

        # anything else ignored

    def start_format_seq(self):
        """A format sequence begins with a 31 and ends with a 10. We
        ignore it completely."""
        while self.getchar() != 10:
            pass

    def convert(self):
        """Performs the actual conversion."""
        skip = 0
        # skip denotes whether to skip the next read and just use
        # what's in this_char (if a function has read ahead, say)
        while 1:
            if not skip:
                self.getchar()
            if self.this_char in self.dispatch_table:
                skip = self.dispatch_table[self.this_char]()
            else:
                skip = self.w_char(chr(self.this_char))
            if self.this_char == -1:
                break
        pass


class RtfConverter(Converter):

    header = (
        r"{\rtf1\ansi\ansicpg1252\deff0"  # Codepage 1252 is almost Latin-1
        r"{\fonttbl"
        r"{\f0\froman\fcharset0\fprq0\cpg1252 Times New Roman}}"
        # We only want one font.
        r"{\stylesheet{\s0\fi360\sb60\sa60\qj 1stWord+ Normal text;}"
        r"{\s1\li720\ri720\qj\sb60\sa60 1stWord+ Indented;}}"
        # These are the only two formatting variants we deal with.
        # Measurement units are "twips", 1/20th of a point.
        r"\sect"
        # Begin section (we'll only have one).
        r"\pgnstart1"
        # Here's an amusing little peculiarity: unless we put a
        # document formatting property control word between \sect and
        # the first \s, OOo ignores the \s and puts the paragraph in
        # the default style. So here we specify (unnecessarily) that
        # the first page number should be 1.
    )

    def w_linefeed(self):
        """We write single linefeeds (for human readability of the
        RTF) and take multiple ones to indicate a new paragraph."""
        if self.run_length == 0:
            if self.prev_char != 30:
                self.outfile.write(" ")
            self.outfile.write("\n")
        if self.run_length < 2 and self.emptyline:
            self.outfile.write("\n\\par")
            # Write the \par here since we don't want a \par at the start
            # of the document.
            self.new_para = 1
        self.emptyline = 1

    def check_new_par(self):
        if self.new_para:
            self.outfile.write("\\s0")
            self.curr_para_style = "normal"
            self.new_para = 0

    def w_char(self, char):
        """Could be the first non-space character after a multiple
        linefeed -- in this case start a new paragraph."""
        self.emptyline = 0
        self.check_new_par()
        self.outfile.write(chr(self.this_char))

    def w_indent(self):
        """We use one indentation style to deal with any amount of
        indentation."""
        indents = 0
        while 1:
            # count the 28s to measure indentation
            c = self.getchar()
            if c != 28:
                break
            indents += 1
        # If the sequence is terminated by a 10, it's an empty line so
        # we ignore it.
        if c != 10 and self.curr_para_style != "indent":
            self.curr_para_style = "indent"
            self.outfile.write("\\s1 ")
            self.new_para = 0
        if c == 10:
            return 0
        else:
            return 1

    def w_textstyle(self, bold, light, italic, underline,
                    superscript, subscript):
        changed = 0
        newstyle = {"b": bold, "i": italic, "ul": underline,
                    "sub": subscript, "super": superscript}
        for style in list(newstyle.keys()):
            if newstyle[style] != self.stylestate[style]:
                changed = 1
                self.outfile.write("\\" + style)
                if newstyle[style] == 0:
                    self.outfile.write("0")
        if changed:
            self.outfile.write(" ")
            self.check_new_par()
            self.stylestate = newstyle

    def finish(self):
        self.outfile.write("}")

    def w_space(self):
        # swallow leading and repeated spaces
        if ((not self.emptyline) and
                self.prev_char not in [0, 10, 27, 28, 29, 30, 32]):
            self.outfile.write(" ")

    def __init__(self, infile, outfile):
        Converter.__init__(self, infile, outfile)
        outfile.write(self.header)
        self.curr_para_style = "none"
        # If Python had enums, curr_para_style would be one. 
        self.new_para = 1
        self.emptyline = 1
        self.stylestate = {"b": 0, "i": 0, "ul": 0, "sub": 0, "super": 0}


def main():
    usage = "Usage: 1wp2rtf ( [-f | --force] <infile> <outfile> | [ -h | --help ] )"
    if (len(sys.argv) == 2 and (sys.argv[1] in ["-h", "--help"])):
        print("1wp2rtf v1.0 (2003-10-20) (c) Pont Lurcock\n" \
              "1wp2rtf converts Acorn 1stWord+ files to RTF files.\n" \
              "1wp2rtf is released under the GNU General Public License, version 3.")
        print(usage)
        print("-h | --help   displays this help text\n" \
              "-f | --force  attempts a conversion even if <infile> doesn't look\n" \
              "              like a 1stWord+ file")
        sys.exit(0)
    force = 0
    if (len(sys.argv) == 4 and sys.argv[1] in ["-f", "--force"]):
        sys.argv.remove(sys.argv[1])
        force = 1
    if (len(sys.argv) == 3):

        infile = open(sys.argv[1], "r", encoding="latin-1")
        firstline = infile.readline()
        if (firstline != "\x1f06601030305800\n"):
            if force:
                print(sys.argv[1], "doesn't look like 1wp, but", \
                    "attempting conversion anyway by your command.")
            else:
                print(sys.argv[1], \
                    "doesn't look like a 1wp file to me, so", \
                    "I'm ignoring it. (Use --force to override.)", file=sys.stderr)
                sys.exit(1)
        infile.close()

        infile = open(sys.argv[1], "rb")
        outfile = open(sys.argv[2], "w")
        con = RtfConverter(infile, outfile)
        con.convert()
        infile.close()
        outfile.close()
        sys.exit(0)
    print("Sorry, I don't understand \"", string.join(sys.argv[1:]), "\".")
    print(usage)
    sys.exit(1)


main()
