import aiohttp
from lib.typehints import NumericStr
from carbon import Carbon as _Carbon, CarbonImage, CarbonOptions


class Carbon(_Carbon):
    def __init__(self, ses: aiohttp.ClientSession):
        super().__init__(ses)

    async def generate_basic_image(self, code: str, first_line_number: int | NumericStr = 1) -> CarbonImage:
        opts: CarbonOptions = CarbonOptions(
            code=code,
            background_color=(0, 0, 0, 0),
            theme='one-dark',
            font_family='JetBrains Mono',
            drop_shadow=False,
            vertical_padding_px=0,
            horizontal_padding_px=0,
            show_line_numbers=True,
            first_line_number=int(first_line_number),
        )
        return await super().generate(opts)
