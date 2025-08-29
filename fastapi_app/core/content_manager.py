import os
import json
import shutil
from pathlib import Path
from ..config import settings

class ContentManager:
    def get_content_list(self, site_name: str):
        if site_name not in settings.data_paths:
            return {"success": False, "message": "Invalid site name"}
        
        data_path = Path(settings.data_paths[site_name])
        if not data_path.exists():
            return {"success": True, "data": []}
        
        folders = []
        for folder in data_path.iterdir():
            if folder.is_dir():
                meta_file = folder / "meta.json"
                pages = []
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                        pages = meta_data.get("urls", [])
                
                folders.append({
                    "date": folder.name,
                    "path": str(folder),
                    "pages": len(pages),
                    "page_list": pages
                })
        
        return {"success": True, "data": sorted(folders, key=lambda x: x["date"], reverse=True)}
    
    def get_content_detail(self, site_name: str, date: str):
        if site_name not in settings.data_paths:
            return {"success": False, "message": "Invalid site name"}
        
        folder_path = Path(settings.data_paths[site_name]) / date
        if not folder_path.exists():
            return {"success": False, "message": "Folder not found"}
        
        content = {"pages": []}
        
        for page_folder in folder_path.iterdir():
            if page_folder.is_dir():
                page_data = {"name": page_folder.name, "files": {"txt": [], "images": []}}
                
                txt_folder = page_folder / "txt"
                if txt_folder.exists():
                    page_data["files"]["txt"] = [f.name for f in txt_folder.glob("*.txt")]
                
                img_folder = page_folder / "image"
                if img_folder.exists():
                    page_data["files"]["images"] = [f.name for f in img_folder.glob("*") if f.is_file()]
                
                content["pages"].append(page_data)
        
        return {"success": True, "data": content}
    
    def delete_content(self, site_name: str, date: str = None):
        if site_name not in settings.data_paths:
            return {"success": False, "message": "Invalid site name"}
        
        if date:
            folder_path = Path(settings.data_paths[site_name]) / date
            if folder_path.exists():
                shutil.rmtree(folder_path)
                return {"success": True, "message": f"Deleted {date}"}
        else:
            data_path = Path(settings.data_paths[site_name])
            if data_path.exists():
                shutil.rmtree(data_path)
                data_path.mkdir(exist_ok=True)
                return {"success": True, "message": f"Deleted all content for {site_name}"}
        
        return {"success": False, "message": "Path not found"}

content_manager = ContentManager()