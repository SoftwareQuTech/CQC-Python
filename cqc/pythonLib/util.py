#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import sys


class ProgressBar:
    def __init__(self, maxitr):
        self.maxitr = maxitr
        self.itr = 0
        try:
            self.cols = os.get_terminal_size().columns
        except (OSError, AttributeError):
            self.cols = 60
        print("")
        self.update()

    def increase(self):
        self.itr += 1
        self.update()

    def update(self):
        cols = self.cols - 8
        assert self.itr <= self.maxitr
        ratio = float(self.itr) / self.maxitr
        procent = int(ratio * 100)
        progress = "=" * int(cols * ratio)
        sys.stdout.write("\r")
        sys.stdout.write("[%*s] %d%%" % (-cols, progress, procent))
        sys.stdout.flush()
        pass

    def close(self):
        print("")


class CQCGeneralError(Exception):
    pass


class CQCNoQubitError(CQCGeneralError):
    pass


class CQCUnsuppError(CQCGeneralError):
    pass


class CQCTimeoutError(CQCGeneralError):
    pass


class CQCInuseError(CQCGeneralError):
    pass


class CQCUnknownError(CQCGeneralError):
    pass


class QubitNotActiveError(CQCGeneralError):
    pass
