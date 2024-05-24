import hashlib
from datetime import datetime
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from src.conf.config import settings
from src.schemas.schemas import AssetType


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
            {'color': 'blue', 'effect': 'outline'}
        ],
        'greyscale': [{'effect': 'grayscale'}],
        'delete_bg': [{'effect': 'bgremoval'}],
        'oil_paint': [{'effect': 'oil_paint:100'}],
        'sepia': [{'effect': 'sepia:100'}],
        'outline': [
            {'width': 500, 'crop': 'scale'},
            {'color': 'darkgrey', 'effect': 'outline:10:200'}
        ]
    }

    def upload_photo(self, file: UploadFile, public_id: str):
        """
        Uploads an image file to Cloudinary with a specified public ID.

        Args:
            file: The image file to upload (of type UploadFile from FastAPI)
            public_id: The unique identifier to assign to the uploaded image in Cloudinary

        Returns:
            A dictionary containing the details of the uploaded image as returned by Cloudinary's upload API.
        """
        return cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)

    def get_photo_url(self, public_id, asset) -> str:
        """
        Generates a URL for the uploaded image with a specific version (asset)

        Args:
            public_id: The unique identifier of the uploaded image in Cloudinary
            asset: A dictionary containing the asset details as returned by Cloudinary's upload API

        Returns:
            A URL string pointing to the uploaded image with the specified version.
        """
        return cloudinary.CloudinaryImage(public_id).build_url(version=asset.get('version'))
    
    def get_unique_file_name(self, filename: str):
        """
        Generates a unique filename for the uploaded image.

        Args:
            filename: The original filename of the uploaded image

        Returns:
            A unique filename string constructed using a hash of the original filename and a timestamp.
        """        
        name =  hashlib.sha256(filename.encode('utf-8')).hexdigest()[:12]
        return f"{name}.{datetime.now().timestamp()}"
    
    def transformate_photo(self, url: str, asset_type: AssetType):
        """
        Applies a transformation to an existing Cloudinary image URL based on the provided asset type.

        Args:
            url: The URL of the existing image in Cloudinary
            asset_type: An enumeration value representing the desired transformation type (e.g., avatar, grayscale)

        Returns:
            A URL string pointing to the transformed version of the image.
        """
        original_url = url
        upload_part = '/upload/'
        start_index = original_url.find(upload_part) + len(upload_part)
        image_name = original_url[start_index:]
        transformed_link = cloudinary.CloudinaryImage(image_name).build_url(transformation=self.transformaitons[asset_type.value])

        return transformed_link
    
CloudPhotoService = CloudPhoto()