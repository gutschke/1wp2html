1wp2rtf: 1stWord+ to RTF Converter
==================================

1stWord+ was an early word processor for 32-bit Acorn computers.
1wp2rtf, as the name implies, converts 1stWord+ files to Rich Text
Format. It's fairly basic: it handles character styles (bold, italic and
so forth) and makes an attempt at handling indented text blocks.

On the input side, I've tested it with the large collection of 1stWord+
files I needed to have converted. On the output side, I've tested the
RTF files with OpenOffice 1.1 and LibreOffice 4.4. If you come across
any conversion problems, please let me know and I will attempt to fix
them.

Usage
-----

    1wp2rtf.py [-f | --force] <infile> <outfile> | [ -h | --help ]
      -h | --help   displays help text
      -f | --force  attempts a conversion even if <infile> doesn't look
                    like a 1stWord+ file

Notes
-----

1wp2rtf is written in Python 2 and has no dependencies apart from the
standard libraries.

[This message](http://www.chiark.greenend.org.uk/~theom/riscos/docs/fancytextformat.txt)
is a useful reference on Fancy Text Format, on which the 1stWord+ format
is based. It was most useful in the production of 1wp2rtf.

Copyright and license
---------------------

Copyright 2003, 2016 Pontus Lurcock (pont at talvi dot net).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
