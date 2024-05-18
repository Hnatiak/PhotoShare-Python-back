import hashlib
from datetime import datetime
from fastapi import Depends, File, UploadFile
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from src.conf.config import settings
from src.entity.models import AssetType


class CloudPhoto:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    transformaitons = {
        'avatar': [
            {'aspect_ratio': '1.0', 'gravity': 'face', 'width': 400, 'zoom': '1', 'crop': 'thumb'},
            {'radius': 'max'},
            {'color': 'grey', 'effect': 'outline'}
        ],
        'grayscale': [{'effect': 'grayscale'}],
        'delete_bg': [{'effect': 'bgremoval'}],
        'oil_paint': [{'effect': 'oil_paint:100'}],
        'sepia': [{'effect': 'sepia:100'}],
        'outline': [
            {'width': 500, 'crop': 'scale'},
            {'color': 'darkgrey', 'effect': 'outline:10:200'}
        ]
    }

    def upload_photo(self, file: UploadFile, public_id: str):
        return cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)

    def get_photo_url(self, public_id, asset) -> str:
        return cloudinary.CloudinaryImage(public_id).build_url(version=asset.get('version'))
    
    def get_unique_file_name(self, filename: str):        
        name =  hashlib.sha256(filename.encode('utf-8')).hexdigest()[:12]
        return f"{name}.{datetime.now().timestamp()}"
    
    def transformate_photo(self, url: str, asset_type: AssetType):
        original_url = url
        upload_part = '/upload/'
        start_index = original_url.find(upload_part) + len(upload_part)
        image_name = original_url[start_index:]
        transformed_link = cloudinary.CloudinaryImage(image_name).build_url(transformation=self.transformaitons[asset_type.value])

        return transformed_link
    
CloudPhotoService = CloudPhoto()