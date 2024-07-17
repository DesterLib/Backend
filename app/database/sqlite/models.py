from tortoise.models import Model
from tortoise import fields, Tortoise

from enum import Enum


class StorageType(Enum):
    LOCAL = "local"
 
    GCS = "gcs"
    AZURE = "azure"
    GDRIVE = "gdrive"

class MediaTypes(Enum):
    MOVIES = "movies"
    TVSHOWS = "tvshows"
    MUSIC = "music"
    OTHERS = "others"


# StorageType.GDRIVE

class Config(Model):
    name = fields.CharField(pk=True, max_length=255)
    value = fields.TextField()

    class Meta:
        table = "config"

class Remote(Model):
    id = fields.CharField(pk=True, max_length=255)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "remotes"


class Collection(Model):
    id = fields.IntField(pk=True, generated=True)
    name = fields.CharField(max_length=255)
    collection_items = fields.ManyToManyField("models.CollectionItem", related_name="collections")
    is_hidden = fields.BooleanField(default=False)
    media_type = fields.CharEnumField(MediaTypes)
    
    class Meta:
        table = "collections"
        
class CollectionItem(Model):
    id = fields.IntField(pk=True, generated=True) # generated
    name = fields.CharField(max_length=255) # filename
    remote = fields.ForeignKeyField("models.Remote", related_name="collection_items") # onedrive
    identifier = fields.CharField(max_length=255) # 1MGsf9vDY9q08C7IO_wcJc_dzAV1DSRZj
    

class Movie(Model):
    id = fields.IntField(pk=True, generated=True)
    name = fields.CharField(max_length=255)
    collection = fields.ForeignKeyField("models.Collection", related_name="movies")
    remote = fields.ForeignKeyField("models.Remote", related_name="movies")
    identifier = fields.CharField(max_length=255)
    is_hidden = fields.BooleanField(default=False)
    media_type = fields.CharEnumField(MediaTypes)
    
    
    class Meta:
        table = "movies"