import requests
import urllib3
import hashlib
import hmac
import time
import json
import base64
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Translator:
    def __init__(self, config):
        self.config = config
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.sessions = {}

    def _get_session(self, mode):
        if mode not in self.sessions:
            session = requests.Session()
            if mode == "manual":
                proxy_url = self.config.get("proxy_url", "http://127.0.0.1:7897")
                session.proxies = {"http": proxy_url, "https": proxy_url}
                session.trust_env = False
            elif mode == "auto":
                session.trust_env = True
            else:
                session.trust_env = False
            self.sessions[mode] = session
        return self.sessions[mode]

    def translate(self, text, target_lang="zh-CN", engine=None):
        if not text: return "No text selected."
        
        # 如果指定了引擎，使用指定的；否则使用配置中的默认引擎
        if engine is None:
            engine = self.config.get("engine", "google")
        
        try:
            if engine == "google":
                return self._google_translate(text, target_lang)
            elif engine == "deepl":
                return self._deepl_translate(text, target_lang)
            elif engine == "tencent":
                return self._tencent_translate(text, target_lang)
            elif engine == "microsoft":
                return self._microsoft_translate(text, target_lang)
            elif engine == "volcano":
                return self._volcano_translate(text, target_lang)
            elif engine == "ai":
                return self._ai_translate(text, target_lang)
        except Exception as e:
            return f"Error: {str(e)}"
        return "Unknown Engine"
    
    def translate_image(self, image_bytes, target_lang="zh-CN", engine=None):
        """图片翻译接口"""
        if not image_bytes:
            return "No image provided."
        
        # 如果指定了引擎，使用指定的；否则使用配置中的图片翻译引擎
        if engine is None:
            engine = self.config.get("image_engine", "tencent")
        
        try:
            if engine == "tencent":
                return self._tencent_image_translate(image_bytes, target_lang)
            elif engine == "ai":
                return self._ai_image_translate(image_bytes, target_lang)
            else:
                return f"引擎 {engine} 不支持图片翻译，请选择腾讯/AI"
        except Exception as e:
            return f"图片翻译失败: {str(e)}"

    def _google_translate(self, text, target_lang="zh-CN"):
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
        
        mode = self.config.get("google_proxy_mode", "auto")
        session = self._get_session(mode)
        
        try:
            res = session.get(url, params=params, headers=self.headers, timeout=10, verify=False)
            res.raise_for_status()
            return "".join([x[0] for x in res.json()[0]])
        except Exception as e:
            return f"Google 翻译失败: {str(e)}"

    def _deepl_translate(self, text, target_lang="zh-CN"):
        api_key = self.config.get("deepl_api_key", "")
        if not api_key:
            return "请在设置中配置 DeepL API Key"
        
        # DeepL 语言代码转换
        lang_map = {"zh-CN": "ZH", "en": "EN-US"}
        target = lang_map.get(target_lang, "ZH")
        
        url = "https://api-free.deepl.com/v2/translate"
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        data = {"text": [text], "target_lang": target}
        
        mode = self.config.get("deepl_proxy_mode", "auto")
        session = self._get_session(mode)
        
        try:
            res = session.post(url, headers=headers, data=data, timeout=10, verify=False)
            res.raise_for_status()
            return res.json()["translations"][0]["text"]
        except Exception as e:
            return f"DeepL 翻译失败: {str(e)}"

    def _tencent_translate(self, text, target_lang="zh-CN"):
        secret_id = self.config.get("tencent_secret_id", "")
        secret_key = self.config.get("tencent_secret_key", "")
        
        if not secret_id or not secret_key:
            return "请在设置中配置腾讯云 SecretId 和 SecretKey"
        
        # 腾讯云语言代码
        lang_map = {"zh-CN": "zh", "en": "en"}
        target = lang_map.get(target_lang, "zh")
        
        endpoint = "tmt.tencentcloudapi.com"
        service = "tmt"
        action = "TextTranslate"
        version = "2018-03-21"
        region = self.config.get("tencent_region", "ap-beijing")
        timestamp = int(time.time())
        
        payload = {
            "SourceText": text,
            "Source": "auto",
            "Target": target,
            "ProjectId": 0
        }
        
        # 腾讯云签名
        canonical_headers = f"content-type:application/json\nhost:{endpoint}\n"
        signed_headers = "content-type;host"
        payload_str = json.dumps(payload)
        canonical_request = f"POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashlib.sha256(payload_str.encode()).hexdigest()}"
        
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        
        def sign(key, msg):
            return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()
        
        secret_date = sign(("TC3" + secret_key).encode(), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
        
        authorization = f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": endpoint,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": region
        }
        
        mode = self.config.get("tencent_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            res = session.post(f"https://{endpoint}", headers=headers, data=payload_str, timeout=10, verify=False)
            res.raise_for_status()
            result = res.json()
            if "Response" in result and "TargetText" in result["Response"]:
                return result["Response"]["TargetText"]
            else:
                return f"腾讯翻译失败: {result.get('Response', {}).get('Error', {}).get('Message', '未知错误')}"
        except Exception as e:
            return f"腾讯翻译失败: {str(e)}"

    def _microsoft_translate(self, text, target_lang="zh-CN"):
        api_key = self.config.get("microsoft_api_key", "")
        region = self.config.get("microsoft_region", "eastasia")
        
        if not api_key:
            return "请在设置中配置 Microsoft API Key"
        
        # 微软语言代码
        lang_map = {"zh-CN": "zh-Hans", "en": "en"}
        target = lang_map.get(target_lang, "zh-Hans")
        
        url = f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={target}"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Ocp-Apim-Subscription-Region": region,
            "Content-Type": "application/json"
        }
        body = [{"text": text}]
        
        mode = self.config.get("microsoft_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            res = session.post(url, headers=headers, json=body, timeout=10, verify=False)
            res.raise_for_status()
            return res.json()[0]["translations"][0]["text"]
        except Exception as e:
            return f"Microsoft 翻译失败: {str(e)}"

    def _volcano_translate(self, text, target_lang="zh-CN"):
        access_key = self.config.get("volcano_access_key", "").strip()
        secret_key = self.config.get("volcano_secret_key", "").strip()
        
        if not access_key or not secret_key:
            return "请在设置中配置火山引擎 AccessKey 和 SecretKey"
        
        # 火山引擎语言代码
        lang_map = {"zh-CN": "zh", "en": "en"}
        target = lang_map.get(target_lang, "zh")
        
        service = "translate"
        version = "2020-06-01"
        action = "TranslateText"
        region = self.config.get("volcano_region", "cn-north-1").strip()
        host = "open.volcengineapi.com"
        
        # 构建请求体
        body = {
            "TargetLanguage": target,
            "TextList": [text]
        }
        body_json = json.dumps(body)
        
        # 火山引擎签名 v4
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        date = timestamp[:8]
        
        # 构建 Canonical Request - 使用字符串拼接避免格式化问题
        canonical_uri = "/"
        canonical_querystring = "Action=" + action + "&Version=" + version
        canonical_headers = "content-type:application/json\nhost:" + host + "\nx-date:" + timestamp + "\n"
        signed_headers = "content-type;host;x-date"
        payload_hash = hashlib.sha256(body_json.encode()).hexdigest()
        canonical_request = "POST\n" + canonical_uri + "\n" + canonical_querystring + "\n" + canonical_headers + "\n" + signed_headers + "\n" + payload_hash
        
        # 构建 String to Sign
        credential_scope = date + "/" + region + "/" + service + "/request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode()).hexdigest()
        string_to_sign = "HMAC-SHA256\n" + timestamp + "\n" + credential_scope + "\n" + hashed_canonical_request
        
        # 计算签名
        def sign(key, msg):
            return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()
        
        k_date = sign(secret_key.encode(), date)
        k_region = sign(k_date, region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, "request")
        signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
        
        # 构建 Authorization Header - 使用字符串拼接避免任何格式化问题
        authorization = "HMAC-SHA256 Credential=" + access_key + "/" + credential_scope + ", SignedHeaders=" + signed_headers + ", Signature=" + signature
        
        headers = {
            "Content-Type": "application/json",
            "Host": host,
            "X-Date": timestamp,
            "Authorization": authorization
        }
        
        mode = self.config.get("volcano_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            url = "https://" + host + "/?" + canonical_querystring
            res = session.post(url, headers=headers, data=body_json, timeout=10, verify=False)
            res.raise_for_status()
            result = res.json()
            
            # 检查是否有错误
            if "ResponseMetadata" in result and "Error" in result["ResponseMetadata"]:
                error_info = result["ResponseMetadata"]["Error"]
                error_code = error_info.get("Code", "Unknown")
                error_msg = error_info.get("Message", "未知错误")
                return "火山翻译失败 [" + error_code + "]: " + error_msg
            
            # 提取翻译结果
            if "TranslationList" in result and len(result["TranslationList"]) > 0:
                return result["TranslationList"][0]["Translation"]
            else:
                return "火山翻译失败: 返回结果格式异常 - " + json.dumps(result, ensure_ascii=False)[:200]
        except requests.exceptions.HTTPError as e:
            return "火山翻译 HTTP 错误: " + str(e.response.status_code) + " - " + e.response.text[:200]
        except Exception as e:
            return "火山翻译失败: " + str(e)

    def _ai_translate(self, text, target_lang="zh-CN"):
        key = self.config.get("ai_api_key")
        base_url = self.config.get("ai_endpoint", "").rstrip('/')
        model = self.config.get("ai_model", "gpt-3.5-turbo")
        prompt = self.config.get("ai_prompt")
        
        # 根据目标语言调整提示词
        if target_lang == "zh-CN":
            lang_instruction = "Translate the following text to Chinese"
        else:
            lang_instruction = "Translate the following text to English"

        if not key: return "Please set AI API Key."
        api_url = base_url if "/chat/completions" in base_url else f"{base_url}/chat/completions"

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "system", "content": f"{lang_instruction}: {prompt}"}, {"role": "user", "content": text}]}
        
        mode = self.config.get("ai_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            res = session.post(api_url, headers=headers, json=data, timeout=30, verify=False)
            if res.status_code != 200:
                return f"AI Error {res.status_code}: {res.text[:200]}"
            return res.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"AI 访问失败: {str(e)}"
    
    # ========== 图片翻译方法 ==========
    
    def _tencent_image_translate(self, image_bytes, target_lang="zh-CN"):
        """腾讯云图片翻译"""
        secret_id = self.config.get("tencent_secret_id", "")
        secret_key = self.config.get("tencent_secret_key", "")
        
        if not secret_id or not secret_key:
            return "请在设置中配置腾讯云 SecretId 和 SecretKey"
        
        # 腾讯云语言代码
        lang_map = {"zh-CN": "zh", "en": "en"}
        target = lang_map.get(target_lang, "zh")
        
        endpoint = "tmt.tencentcloudapi.com"
        service = "tmt"
        action = "ImageTranslate"
        version = "2018-03-21"
        region = self.config.get("tencent_region", "ap-beijing")
        timestamp = int(time.time())
        
        # 将��片转为 base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "SessionUuid": str(int(time.time() * 1000)),
            "Scene": "doc",
            "Data": image_base64,
            "Source": "auto",
            "Target": target,
            "ProjectId": 0
        }
        
        # 腾讯云签名
        canonical_headers = f"content-type:application/json\nhost:{endpoint}\n"
        signed_headers = "content-type;host"
        payload_str = json.dumps(payload)
        canonical_request = f"POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashlib.sha256(payload_str.encode()).hexdigest()}"
        
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        
        def sign(key, msg):
            return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()
        
        secret_date = sign(("TC3" + secret_key).encode(), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
        
        authorization = f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": endpoint,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": region
        }
        
        mode = self.config.get("tencent_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            res = session.post(f"https://{endpoint}", headers=headers, data=payload_str, timeout=30, verify=False)
            res.raise_for_status()
            result = res.json()
            if "Response" in result and "ImageRecord" in result["Response"]:
                # 提取所有文本块
                records = result["Response"]["ImageRecord"]["Value"]
                translated_texts = [item["TargetText"] for item in records]
                return "\n".join(translated_texts)
            else:
                return f"腾讯图片翻译失败: {result.get('Response', {}).get('Error', {}).get('Message', '未知错误')}"
        except Exception as e:
            return f"腾讯图片翻译失败: {str(e)}"
    
    def _ai_image_translate(self, image_bytes, target_lang="zh-CN"):
        """AI 大模型图片翻译（支持 GPT-4V 等视觉模型）"""
        key = self.config.get("ai_api_key")
        base_url = self.config.get("ai_endpoint", "").rstrip('/')
        model = self.config.get("ai_model", "gpt-4-vision-preview")
        
        if not key:
            return "请在设置中配置 AI API Key"
        
        # 根据目标语言调整提示词
        if target_lang == "zh-CN":
            lang_instruction = "请识别图片中的所有文字并翻译成中文，只输出翻译结果，不要有其他说明。"
        else:
            lang_instruction = "Please recognize all text in the image and translate it to English. Output only the translation without any explanation."
        
        api_url = base_url if "/chat/completions" in base_url else f"{base_url}/chat/completions"
        
        # 将图片转为 base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": lang_instruction},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        mode = self.config.get("ai_proxy_mode", "direct")
        session = self._get_session(mode)
        
        try:
            res = session.post(api_url, headers=headers, json=data, timeout=60, verify=False)
            if res.status_code != 200:
                return f"AI 图片翻译错误 {res.status_code}: {res.text[:200]}"
            return res.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"AI 图片翻译失败: {str(e)}"
