-- 创建爬虫任务表
CREATE TABLE crawler_tasks (
    id SERIAL PRIMARY KEY,
    site_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'stopped',  -- running, stopped, error
    pid INTEGER,
    start_time TIMESTAMPTZ,
    last_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 为爬虫任务表创建索引
CREATE INDEX idx_crawler_tasks_site_name ON crawler_tasks(site_name);
CREATE INDEX idx_crawler_tasks_status ON crawler_tasks(status);
CREATE INDEX idx_crawler_tasks_last_run ON crawler_tasks(last_run);

-- 添加注释
COMMENT ON TABLE crawler_tasks IS '爬虫任务管理表';
COMMENT ON COLUMN crawler_tasks.site_name IS '网站名称';
COMMENT ON COLUMN crawler_tasks.status IS '任务状态：running-运行中, stopped-已停止, error-错误';
COMMENT ON COLUMN crawler_tasks.pid IS '进程ID';
COMMENT ON COLUMN crawler_tasks.start_time IS '任务启动时间';
COMMENT ON COLUMN crawler_tasks.last_run IS '最后运行时间';

-- 创建审核任务表
CREATE TABLE audit_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    site_name VARCHAR(255) NOT NULL,
    date_folder VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    results TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- 为审核任务表创建索引
CREATE INDEX idx_audit_tasks_task_id ON audit_tasks(task_id);
CREATE INDEX idx_audit_tasks_site_name ON audit_tasks(site_name);
CREATE INDEX idx_audit_tasks_status ON audit_tasks(status);
CREATE INDEX idx_audit_tasks_created_at ON audit_tasks(created_at);
CREATE INDEX idx_audit_tasks_date_folder ON audit_tasks(date_folder);

-- 添加注释
COMMENT ON TABLE audit_tasks IS '审核任务表';
COMMENT ON COLUMN audit_tasks.task_id IS '任务唯一标识';
COMMENT ON COLUMN audit_tasks.site_name IS '网站名称';
COMMENT ON COLUMN audit_tasks.date_folder IS '日期文件夹';
COMMENT ON COLUMN audit_tasks.status IS '任务状态：pending-待处理, running-运行中, completed-已完成, failed-失败';
COMMENT ON COLUMN audit_tasks.progress IS '进度百分比(0-100)';
COMMENT ON COLUMN audit_tasks.results IS '审核结果(JSON格式)';

-- 创建审核结果表
CREATE TABLE audit_url_results (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    site_name VARCHAR(255) NOT NULL,
    date_folder VARCHAR(255) NOT NULL,
    page_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'text')),
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    
    -- 审核结果字段
    is_sensitive BOOLEAN DEFAULT FALSE,
    confidence DECIMAL(5,4),  -- 0.0000 到 1.0000
    
    -- 图片审核结果
    is_abnormal_window BOOLEAN,
    window_confidence DECIMAL(5,4),
    
    -- 色情内容检测分数 (0.0000 到 1.0000)
    drawings_score DECIMAL(5,4),
    hentai_score DECIMAL(5,4),
    neutral_score DECIMAL(5,4),
    porn_score DECIMAL(5,4),
    sexy_score DECIMAL(5,4),
    
    -- 文本审核结果
    sensitive_words TEXT,  -- JSON数组格式存储敏感词
    
    -- OCR结果
    ocr_text TEXT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 原始审核响应（JSON格式）
    raw_response JSONB,
    
    -- 外键约束
    FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
);

-- 为审核结果表创建索引
CREATE INDEX idx_audit_url_results_task_id ON audit_url_results(task_id);
CREATE INDEX idx_audit_url_results_site_name ON audit_url_results(site_name);
CREATE INDEX idx_audit_url_results_date_folder ON audit_url_results(date_folder);
CREATE INDEX idx_audit_url_results_file_type ON audit_url_results(file_type);
CREATE INDEX idx_audit_url_results_is_sensitive ON audit_url_results(is_sensitive);
CREATE INDEX idx_audit_url_results_created_at ON audit_url_results(created_at);
CREATE INDEX idx_audit_url_results_confidence ON audit_url_results(confidence);

-- 为JSONB字段创建GIN索引（提高JSON查询性能）
CREATE INDEX idx_audit_url_results_raw_response_gin ON audit_url_results USING GIN (raw_response);

-- 添加注释
COMMENT ON TABLE audit_url_results IS '审核结果详细表';
COMMENT ON COLUMN audit_url_results.task_id IS '关联的审核任务ID';
COMMENT ON COLUMN audit_url_results.site_name IS '网站名称';
COMMENT ON COLUMN audit_url_results.date_folder IS '日期文件夹';
COMMENT ON COLUMN audit_url_results.page_name IS '页面名称';
COMMENT ON COLUMN audit_url_results.file_type IS '文件类型：image-图片, text-文本';
COMMENT ON COLUMN audit_url_results.file_path IS '文件完整路径';
COMMENT ON COLUMN audit_url_results.file_name IS '文件名';
COMMENT ON COLUMN audit_url_results.is_sensitive IS '是否为敏感内容';
COMMENT ON COLUMN audit_url_results.confidence IS '整体置信度(0-1)';
COMMENT ON COLUMN audit_url_results.is_abnormal_window IS '是否为异常窗口';
COMMENT ON COLUMN audit_url_results.window_confidence IS '窗口检测置信度(0-1)';
COMMENT ON COLUMN audit_url_results.drawings_score IS '绘画内容分数(0-1)';
COMMENT ON COLUMN audit_url_results.hentai_score IS 'H内容分数(0-1)';
COMMENT ON COLUMN audit_url_results.neutral_score IS '正常内容分数(0-1)';
COMMENT ON COLUMN audit_url_results.porn_score IS '色情内容分数(0-1)';
COMMENT ON COLUMN audit_url_results.sexy_score IS '性感内容分数(0-1)';
COMMENT ON COLUMN audit_url_results.sensitive_words IS '检测到的敏感词(JSON数组)';
COMMENT ON COLUMN audit_url_results.ocr_text IS 'OCR识别的文字内容';
COMMENT ON COLUMN audit_url_results.raw_response IS '原始API响应(JSON格式)';

-- 创建触发器函数：自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为各表创建自动更新时间戳的触发器
CREATE TRIGGER update_crawler_tasks_updated_at
    BEFORE UPDATE ON crawler_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_tasks_updated_at
    BEFORE UPDATE ON audit_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_url_results_updated_at
    BEFORE UPDATE ON audit_url_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

