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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from cqc.cqcHeader import (
    CQCCmdHeader,
    CQCHeader,
    CQCTypeHeader,
    CQCAssignHeader,
    CQCFactoryHeader,
    CQCIfHeader,
    CQCXtraQubitHeader,
    CQCType,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_MEASURE,
    CQC_CMD_MEASURE_INPLACE,
)


def parse_cqc_message(msg):
    # TODO finish parser
    hdr_map = {
        CQCType.HELLO: None,
        CQCType.COMMAND: CQCCmdHeader,
        CQCType.MIX: CQCTypeHeader,
        CQCType.IF: CQCIfHeader,
        CQCType.FACTORY: CQCFactoryHeader,
    }
    headers = []
    next_hdr = CQCHeader
    bits_to_next_first_hdr = 0
    is_mix = False
    while len(msg) > 0:
        hdr = extract_header(msg, next_hdr)
        headers.append(hdr)
        next_hdr = None
        msg = msg[hdr.HDR_LENGTH:]
        if isinstance(hdr, CQCHeader):
            bits_to_next_first_hdr = hdr.length
            next_hdr = hdr_map[hdr.tp]
            is_mix = hdr.tp == CQCType.MIX
        else:
            if isinstance(hdr, CQCCmdHeader):
                if hdr.instr in [CQC_CMD_MEASURE, CQC_CMD_MEASURE_INPLACE]:
                    next_hdr = CQCAssignHeader
                if hdr.instr in [CQC_CMD_CNOT, CQC_CMD_CPHASE]:
                    next_hdr = CQCXtraQubitHeader
            elif isinstance(hdr, CQCTypeHeader):
                next_hdr = hdr_map[hdr.type]
            elif isinstance(hdr, CQCAssignHeader):
                pass
            elif isinstance(hdr, CQCIfHeader):
                pass
            elif isinstance(hdr, CQCXtraQubitHeader):
                pass
            elif isinstance(hdr, CQCFactoryHeader):
                next_hdr = CQCCmdHeader
            else:
                raise NotImplementedError("for {}".format(hdr))
            bits_to_next_first_hdr -= hdr.HDR_LENGTH
        if bits_to_next_first_hdr <= 0:
            next_hdr = CQCHeader
        if next_hdr is None:
            if is_mix:
                next_hdr = CQCTypeHeader
            else:
                next_hdr = CQCCmdHeader

    return headers


def extract_header(msg, hdr_class):
    hdr = hdr_class(msg[:hdr_class.HDR_LENGTH])
    return hdr
