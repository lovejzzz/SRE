import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/software-resynthesis/scripts'))
import sre_journal


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'project.json').write_text(json.dumps({'schema_version':1,'request':'Full game including art','features':[]}))
        (self.root/'capture.json').write_text('{"actual":true}')
        self.entry = {'schema_version':1,'id':'001-import','title':'Import','objective':'Read assets',
                      'outcome':'progress','actions':['Read texture pack'],'difficulties':['Missing decoder'],
                      'resolutions':['Implemented bounded parser'],'limitations':['No runtime fidelity'],
                      'result':'Loaded images','next_action':'Inspect actual render',
                      'evidence':[{'path':'capture.json','description':'Decoder output'}]}

    def record(self):
        path=self.root/'input.json';path.write_text(json.dumps(self.entry))
        return sre_journal.record(self.root,path)

    def test_record_preserves_history_and_scope(self):
        self.record()
        with self.assertRaises(FileExistsError): self.record()
        report, problems=sre_journal.report(self.root)
        self.assertFalse(problems)
        self.assertIn('Full game including art',report)
        self.assertIn('No runtime fidelity',report)
        self.assertIn('not a fidelity or acceptance certificate',report)

    def test_modified_capture_is_reported(self):
        self.record();(self.root/'capture.json').write_text('{"actual":false}')
        report, problems=sre_journal.report(self.root)
        self.assertEqual(len(problems),1)
        self.assertIn('stale',report)

    def test_traversal_and_symlink_are_rejected(self):
        self.entry['evidence'][0]['path']='../outside'
        with self.assertRaises(ValueError): self.record()
        (self.root/'escape').symlink_to('/etc/hosts')
        self.entry['evidence'][0]['path']='escape'
        with self.assertRaises(ValueError): self.record()

    def test_missing_record_digest_is_reported_without_crash(self):
        self.record()
        path=self.root/'journal/001-import.json'
        entry=json.loads(path.read_text());del entry['evidence'][0]['sha256']
        path.write_text(json.dumps(entry))
        report,problems=sre_journal.report(self.root)
        self.assertEqual(len(problems),1)
        self.assertIn('MISSING',report)

    def test_unsafe_id_and_unbacked_verification_are_rejected(self):
        self.entry['id']='../../escape'
        with self.assertRaises(ValueError): self.record()
        self.entry['id']='valid';self.entry['outcome']='verified';self.entry['evidence']=[]
        with self.assertRaises(ValueError): self.record()


if __name__=='__main__': unittest.main()
