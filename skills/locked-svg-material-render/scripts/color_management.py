"""Explicit input-profile conversion. No automatic wide-gamut relabeling."""
import hashlib
from io import BytesIO
from PIL import ImageCms


def convert_srgb(image, assume_srgb=False):
    target = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    embedded = image.info.get('icc_profile')
    alpha = image.convert('RGBA').getchannel('A')
    record = {'output_profile_sha256': hashlib.sha256(target.tobytes()).hexdigest()}
    if embedded:
        source = ImageCms.ImageCmsProfile(BytesIO(embedded))
        rgb = ImageCms.profileToProfile(image.convert('RGB'), source, target, outputMode='RGB', renderingIntent=0)
        record.update(operation='icc_conversion', input_profile=ImageCms.getProfileDescription(source).strip(), input_profile_sha256=hashlib.sha256(embedded).hexdigest())
    elif 'srgb' in image.info:
        rgb = image.convert('RGB')
        record.update(operation='declared_srgb', input_profile='PNG sRGB chunk')
    elif assume_srgb:
        rgb = image.convert('RGB')
        record.update(operation='explicit_srgb_assumption', input_profile='untagged; caller explicitly assumes sRGB')
    else:
        raise ValueError('Untagged material: declare --assume-srgb only when justified; embedded profiles are always converted')
    rgb.putalpha(alpha)
    return rgb, target.tobytes(), record
