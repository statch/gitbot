import aiohttp
from carbon import Carbon as _Carbon, CarbonImage, CarbonOptions


class Carbon(_Carbon):
    def __init__(self, ses: aiohttp.ClientSession):
        super().__init__(session=ses)

    async def generate_basic_image(self, code: str) -> CarbonImage:
        opts: CarbonOptions = CarbonOptions(
            code=code,
            background_color=(0, 0, 0, 0),
            theme='one-dark',
            font_family='JetBrains Mono',
            drop_shadow=False,
            vertical_padding_px=0,
            horizontal_padding_px=0,
            show_line_numbers=True
        )
        return await super().generate(opts)
