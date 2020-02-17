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
                raise NotImplementedError(f"for {hdr}")
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
