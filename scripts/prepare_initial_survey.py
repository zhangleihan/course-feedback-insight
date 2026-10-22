#!/usr/bin/env python3
"""将教师原始导出转为受限教学数据；不生成原身份映射，不调用外部服务。"""
import argparse
import collections
import json
import random
import re
from pathlib import Path

OPEN = {'q1','q2','q3','q3verify','q4tools','q5','q6example','q7','q8example',
        'q10','q12','q13','q14','q15why','q16why','q17','q18extra'}
SINGLE = {'q4','q16','q16format'}
MULTI = {'q6','q8','q9','q15','q17support','q18'}
SENSITIVE = re.compile(r'我的健康|经期|心理问题|心情|急救|抽搐|我的收入|没钱花|呋虫胺|臭虫')
GENERALIZE = [
 (r'藏区','[特定地区]'),(r'藏文','[特定语言]'),
 (r'暑假实习','一次实践活动'),(r'债券定价模型','专业分析模型'),
 (r'企业经营模拟比赛|企业模拟大赛','课程实践活动'),
 (r'会计学|公司金融','某门课程'),(r'主持一项大创','参与一项学生项目'),
 (r'agentlab','自建工具'),(r'自动抽取塔罗牌','交互式内容生成'),
 (r'U\s*盘','存储设备'),(r'小猫壁纸','个性化界面'),
]

def prepare(source):
 rows=source.get('records')
 if not isinstance(rows,list):raise ValueError('输入须包含records数组')
 identifiers=sorted({str(r.get(k) or '').strip() for r in rows for k in ['name','student_number','id']
                     if len(str(r.get(k) or '').strip())>=2},key=len,reverse=True)
 edits=collections.Counter()
 def redact(value):
  text=value
  for token in identifiers:
   if token in text:edits['identity']+=text.count(token);text=text.replace(token,'[身份信息已删除]')
  patterns=[(r'https?://[^\s\u3000]+','[链接已删除]'),
            (r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[邮箱已删除]'),
            (r'(?<!\d)1[3-9]\d{9}(?!\d)','[电话已删除]'),
            (r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[网络地址已删除]'),
            (r'(?i)\bsk-[A-Za-z0-9_-]{12,}','[密钥已删除]'),
            (r'(?<!\d)\d{17}[\dXx](?!\d)','[证件号码已删除]'),
            (r'(?:微信号|QQ号|联系电话|手机号|学号|姓名)\s*[:：]\s*[^\s，。；;]+','[联系方式或身份已删除]')]
  for pattern,replacement in patterns:
   text,n=re.subn(pattern,replacement,text);edits['pattern']+=n
  if SENSITIVE.search(text):edits['sensitive_field']+=1;return '[涉及个人敏感经历，已移除细节]'
  for pattern,replacement in GENERALIZE:
   text,n=re.subn(pattern,replacement,text,flags=re.I);edits['generalized']+=n
  return text
 # 同一身份仅保留最新已提交且允许保存的版本。先选最新版本，再检查AI同意，避免恢复旧许可。
 latest={}
 for r in sorted(rows,key=lambda r:r.get('updatedAt') or r.get('updated_at') or ''):
  if r.get('status')=='submitted':latest[str(r.get('student_number') or r.get('id'))]=r
 selected=[r for r in latest.values() if r.get('consents',{}).get('store') is True and r.get('consents',{}).get('ai') is True]
 random.SystemRandom().shuffle(selected)
 records=[]
 for i,r in enumerate(selected,1):
  answers={};a=r.get('answers',{})
  for key,value in a.items():
   if key in OPEN and isinstance(value,str):answers[key]=redact(value)
   elif key in SINGLE and isinstance(value,str):answers[key]=redact(value)
   elif key in MULTI and isinstance(value,list):answers[key]=[redact(v) for v in value if isinstance(v,str)]
   elif key=='q11' and isinstance(value,dict):answers[key]={redact(k):redact(v) for k,v in value.items() if isinstance(k,str) and isinstance(v,str)}
  followups=[]
  for j,f in enumerate(r.get('followups') or [],1):
   if f.get('qid') not in OPEN:continue
   answer=f.get('answer');answer=redact(answer) if isinstance(answer,str) else None
   skipped=f.get('skipped') is True
   followups.append({'followup_id':f'F{j:02d}','question_id':f['qid'],
    'question':redact(f.get('question') or ''),'answer':answer,'skipped':skipped,
    'response_status':'skipped' if skipped else ('answered' if answer and answer.strip() else 'unanswered')})
  experienced=any(any(x in s for x in ['用过别人','配置过','修改过','用代码']) for s in a.get('q9',[]) if isinstance(s,str))
  records.append({'participant_id':f'P{i:03d}','answers':answers,'question_variants':{
   'q5':'nonuse_reason' if a.get('q4')=='从未使用过' else 'usage_experience',
   'q10':'agent_experience' if experienced else 'desired_workflow'},'followups':followups})
 package={'schema_version':'1.0','dataset_id':'course-start-initial-restricted-v1',
  'data_type':'real_survey_deidentified','stage':'course_start','access':'restricted_teaching',
  'public_release':False,'contains_verbatim_or_generalized_text':True,
  'note':'脱敏文本保留缺失与不确定回答；少量敏感内容移除或泛化，不是不可重识别保证。编号每次重建随机排列，不跨版本关联。',
  'record_count':len(records),'records':records}
 report={'input_records':len(rows),'submitted_records':sum(r.get('status')=='submitted' for r in rows),
  'included_records':len(records),'followup_items':sum(len(r['followups']) for r in records),
  'answered_followups':sum(f['response_status']=='answered' for r in records for f in r['followups']),
  'redaction_counts':dict(edits),'removed_fields':['name','student_number','original_id','timestamps','analysis','step','follow_count','followup_basis','original_followup_id'],
  'identity_mapping_saved':False,'external_model_calls':0}
 # 输出前再检验直接身份与常见联系方式；不记录命中的原值。
 serialized=json.dumps(package,ensure_ascii=False)
 if any(token in serialized for token in identifiers):raise ValueError('输出仍包含直接身份标识')
 if re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)1[3-9]\d{9}(?!\d)',serialized):raise ValueError('输出仍包含联系方式')
 return package,report

def text_units(package):
 for r in package['records']:
  pid=r['participant_id']
  for qid,text in r['answers'].items():
   if qid in OPEN and isinstance(text,str) and text.strip():
    yield {'unit_id':f'{pid}-{qid}','participant_id':pid,'source':'main_answer','question_id':qid,'question_variant':r['question_variants'].get(qid),'text':text}
  for f in r['followups']:
   if f['response_status']=='answered':yield {'unit_id':f'{pid}-{f["question_id"]}-{f["followup_id"]}',
    'participant_id':pid,'source':'followup_answer','question_id':f['question_id'],'question_variant':r['question_variants'].get(f['question_id']),'question':f['question'],'text':f['answer']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data/raw/initial-survey');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 package,report=prepare(json.loads(a.input.read_text(encoding='utf-8')))
 (a.output/'feedback.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
 units=list(text_units(package));(a.output/'text_units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
 report['text_units']=len(units);(a.output/'processing_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='removed_fields'},ensure_ascii=False))
if __name__=='__main__':main()
