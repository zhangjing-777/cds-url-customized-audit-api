import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from ..database import AuditResult
from ..config import settings

# 导入现有的审核客户端
import sys
sys.path.append('.')
from hx_client import BackendClient

logger = logging.getLogger(__name__)

class DatabaseAuditClient:
    def __init__(self):
        self.client = BackendClient()
    
    def process_site_with_db(self, task_id: str, site_name: str, date_folder: str, folder_path: str, db: Session):
        """处理网站内容并将结果存入数据库"""
        folder_path = Path(folder_path)
        
        # 读取meta.json获取页面信息
        meta_file = folder_path / "meta.json"
        if not meta_file.exists():
            logger.warning(f"meta.json not found in {folder_path}")
            return
        
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
            pages = meta_data.get("urls", [])
        
        # 处理每个页面
        for page in pages:
            page_name = page.get('name', '')
            url = page.get('url', '')
            
            page_folder = folder_path / page_name
            if not page_folder.exists():
                continue
            
            # 处理图片
            img_folder = page_folder / "image"
            if img_folder.exists():
                self._process_images(task_id, site_name, date_folder, page_name, url, img_folder, db)
            
            # 处理文本
            txt_folder = page_folder / "txt"
            if txt_folder.exists():
                self._process_texts(task_id, site_name, date_folder, page_name, url, txt_folder, db)
    
    def _process_images(self, task_id: str, site_name: str, date_folder: str, page_name: str, url: str, img_folder: Path, db: Session):
        """处理图片文件"""
        for img_file in img_folder.glob("*"):
            if not img_file.is_file():
                continue
            
            try:
                # 调用图片审核
                result = self.client.predict_all(str(img_file), url)
                
                # 解析审核结果
                audit_result = AuditResult(
                    task_id=task_id,
                    site_name=site_name,
                    date_folder=date_folder,
                    page_name=page_name,
                    file_type="image",
                    file_path=str(img_file),
                    file_name=img_file.name,
                    raw_response=json.dumps(result, ensure_ascii=False)
                )
                
                # 解析具体字段
                if 'window_result' in result:
                    window_result = result['window_result']
                    audit_result.is_abnormal_window = window_result.get('is_abnormal', False)
                    audit_result.window_confidence = window_result.get('confidence', 0.0)
                
                if 'sex_result' in result:
                    sex_result = result['sex_result']['sex_model_result']
                    audit_result.drawings_score = sex_result.get('drawings', 0.0)
                    audit_result.hentai_score = sex_result.get('hentai', 0.0)
                    audit_result.neutral_score = sex_result.get('neutral', 0.0)
                    audit_result.porn_score = sex_result.get('porn', 0.0)
                    audit_result.sexy_score = sex_result.get('sexy', 0.0)
                    
                    # 判断是否敏感（porn + sexy + hentai > 0.5）
                    sensitive_score = sex_result.get('porn', 0) + sex_result.get('sexy', 0) + sex_result.get('hentai', 0)
                    audit_result.is_sensitive = sensitive_score > 0.5
                    audit_result.confidence = sensitive_score
                
                if 'ocr_result' in result:
                    ocr_texts = [item.get('text', '') for item in result['ocr_result']['result']]
                    audit_result.ocr_text = ' '.join(ocr_texts)
                
                db.add(audit_result)
                
            except Exception as e:
                logger.error(f"Error processing image {img_file}: {str(e)}")
        
        db.commit()
    
    def _process_texts(self, task_id: str, site_name: str, date_folder: str, page_name: str, url: str, txt_folder: Path, db: Session):
        """处理文本文件"""
        for txt_file in txt_folder.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 按行处理文本
                for line_no, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 调用文本审核
                    result = self.client.predict_dfa([line], url)
                    
                    # 创建审核结果记录
                    audit_result = AuditResult(
                        task_id=task_id,
                        site_name=site_name,
                        date_folder=date_folder,
                        page_name=page_name,
                        file_type="text",
                        file_path=f"{txt_file}:line_{line_no}",
                        file_name=f"{txt_file.name}_line_{line_no}",
                        raw_response=json.dumps(result.result, ensure_ascii=False)
                    )
                    
                    # 解析文本审核结果
                    if result.result:
                        sensitive_words = []
                        for item in result.result:
                            if item.get('sensitive', False):
                                audit_result.is_sensitive = True
                                sensitive_words.extend(item.get('sensitive_words', []))
                        
                        audit_result.sensitive_words = ','.join(sensitive_words) if sensitive_words else None
                        audit_result.confidence = 1.0 if audit_result.is_sensitive else 0.0
                    
                    db.add(audit_result)
                
            except Exception as e:
                logger.error(f"Error processing text {txt_file}: {str(e)}")
        
        db.commit()

audit_client = DatabaseAuditClient()