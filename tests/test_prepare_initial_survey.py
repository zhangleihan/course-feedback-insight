import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare_initial_survey',ROOT/'scripts/prepare_initial_survey.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def record(**updates):
 r={'id':'original-record-111','name':'测试受访者甲','student_number':'202600123456',
    'status':'submitted','consents':{'store':True,'ai':True},'updatedAt':'2026-10-01',
    'answers':{'q5':'我在练习编程。','q9':['听说过但没有用过'],'q10':'想做工具。'},'followups':[]}
 r.update(updates);return r
class PreparationTests(unittest.TestCase):
 def test_only_explicitly_consented_submitted_records(self):
  rows=[record(),record(id='draft',student_number='draft',status='draft'),record(id='no-ai',student_number='no-ai',consents={'store':True,'ai':False}),record(id='no-store',student_number='no-store',consents={'store':False,'ai':True})]
  p,_=m.prepare({'records':rows});self.assertEqual(p['record_count'],1)
 def test_latest_submission_controls_ai_consent(self):
  p,_=m.prepare({'records':[record(),record(updatedAt='2026-10-02',consents={'store':True,'ai':False})]});self.assertEqual(p['record_count'],0)
 def test_remove_identifiers_even_inside_nested_text(self):
  r=record(answers={'q5':'测试受访者甲 202600123456 original-record-111 13812345678 a.person@example.com','q11':{'Python基础':'跟着示例完成'}})
  p,_=m.prepare({'records':[r]});s=json.dumps(p,ensure_ascii=False)
  for value in ['测试受访者甲','202600123456','original-record-111','13812345678','a.person@example.com']:self.assertNotIn(value,s)
  self.assertNotIn('updatedAt',s);self.assertNotIn('student_number',s)
 def test_drop_analysis_and_unknown_answer_fields(self):
  p,_=m.prepare({'records':[record(answers={'q1':'不清楚','secret_field':'should not appear'},analysis={'private':'secret'})]});self.assertEqual(p['records'][0]['answers'],{'q1':'不清楚'})
 def test_preserve_missing_and_uncertainty(self):
  p,_=m.prepare({'records':[record(answers={'q1':'','q2':'暂时不清楚'})]});self.assertEqual(p['records'][0]['answers'],{'q1':'','q2':'暂时不清楚'});self.assertEqual(len(list(m.text_units(p))),1)
 def test_keep_branch_meanings(self):
  p,_=m.prepare({'records':[record(answers={'q4':'从未使用过','q9':[],'q10':'想做工具'})]});self.assertEqual(p['records'][0]['question_variants'],{'q5':'nonuse_reason','q10':'desired_workflow'})
 def test_followup_states_and_hidden_basis(self):
  fs=[{'id':'old-id','qid':'q5','question':'过程呢？','basis':'private basis','answer':'','skipped':False},{'qid':'q5','question':'怎样检查？','answer':'运行测试','skipped':False},{'qid':'q5','question':'例子？','answer':'不使用','skipped':True}]
  p,_=m.prepare({'records':[record(followups=fs)]});f=p['records'][0]['followups'];self.assertEqual([x['response_status'] for x in f],['unanswered','answered','skipped']);self.assertNotIn('basis',json.dumps(p));self.assertNotIn('old-id',json.dumps(p));self.assertEqual(sum(x['source']=='followup_answer' for x in m.text_units(p)),1)
 def test_sensitive_experience_removed(self):
  p,_=m.prepare({'records':[record(answers={'q5':'我曾查询急救信息，并描述了个人经历。'})]});self.assertEqual(p['records'][0]['answers']['q5'],'[涉及个人敏感经历，已移除细节]')
 def test_public_fragments_are_unlinked_paraphrases(self):
  rows=[json.loads(line) for line in (ROOT/'data/samples/teaching_fragments.jsonl').read_text().splitlines()];self.assertEqual(len(rows),24);self.assertEqual(len({r['unit_id'] for r in rows}),24)
  for r in rows:self.assertEqual(r['data_type'],'generalized_teaching_paraphrase');self.assertNotIn('participant_id',r)
 def test_interview_permissions_default_false(self):
  t=json.loads((ROOT/'examples/group_interview.template.json').read_text());self.assertTrue(all(v is False for v in t['consents'].values()))
if __name__=='__main__':unittest.main()
