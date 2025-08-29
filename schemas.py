from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

# ---------- user schemas ----------
class UserBase(BaseModel):
    username:str
    password:str
    email:str

class UserDisplay(BaseModel):
    username:str
    email:str

    class Config:
        from_attributes = True

class UserAuth(BaseModel):
    username:str
    password:str
    email:str



# ---------- content schemas ----------
class BboxInfo(BaseModel):
    text: str
    confidence: float = None
    topleft: List = None
    topright: List = None
    bottomright: List = None
    bottomleft: List = None

class SexInfo(BaseModel):
    sex_model_result:Dict[str,float]

class TextInfo(BaseModel):
    result:List[Dict]

class AbnWindowInfo(BaseModel):
    confidence:float
    is_abnormal:bool

class OcrResponse(BaseModel):
    result: List[BboxInfo]

class Base64Input(BaseModel):
    image:str
    ip_address: Optional[str] = None

class TextInput(BaseModel):
    text:List[str]

# --------- output schemas-------------
class TextOut(BaseModel):
    ip_address:Optional[str] = None
    create_time:datetime
    text:str
    sensitive:bool
    sensitive_words:str
    image_path:Optional[str] = None

    class Config:
        from_attributes = True

class WindowOut(BaseModel):
    ip_address:Optional[str] = None
    create_time:datetime
    confidence:float
    is_abnormal:bool
    image_path:Optional[str] = None
    

    class Config:
        from_attributes = True

class SexOut(BaseModel):
    ip_address:Optional[str] = None
    create_time:datetime
    is_abnormal:bool
    drawings:float
    hentai:float
    neutral:float
    porn:float
    sexy:float
    image_path:Optional[str] = None

    class Config:
        from_attributes = True


class ImagePathInput(BaseModel):
    full_path:str
    
    
class Base64Output(BaseModel):
    b64_image:str