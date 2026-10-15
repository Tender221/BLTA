import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackageReplayTests(unittest.TestCase):
    def test_main_table_is_recomputed_from_portable_inputs(self):
        self.assertTrue((ROOT/'reproduce.py').exists(), 'Portable reproduction entry is not implemented')
        with tempfile.TemporaryDirectory() as folder:
            process = subprocess.run([sys.executable,str(ROOT/'reproduce.py'),'--output',folder],cwd=folder,capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr[-3000:])
            receipt=json.loads((Path(folder)/'verification.json').read_text())
            self.assertEqual(receipt['held_tool_folds'],90)
            self.assertEqual(receipt['source_or_target_partition_violations'],0)
            self.assertEqual(receipt['archived_count_mismatches'],0)
            rows=list(csv.DictReader((Path(folder)/'cross_tool.csv').read_text(encoding='utf-8').splitlines()))
            wolf=next(r for r in rows if r['detector']=='wolf' and r['method']=='global_recenter')
            self.assertEqual(int(wolf['pooled_fp']),167)
            self.assertEqual(int(wolf['pooled_tp']),960)
            self.assertEqual(receipt['agent_outcome_rows'],2688)

    def test_archive_runs_outside_the_research_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            # Build from this checkout. No sibling manuscript directory or
            # pre-existing research archive is required by a fresh clone.
            archive=Path(folder)/'portable.zip'
            files=[ROOT/name for name in ['blta.py','reproduce.py','input_manifest.json']]
            files += [p for directory in ['data','third_party'] for p in (ROOT/directory).rglob('*') if p.is_file()]
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
                for path in files:
                    z.write(path,'BLTA_reproduction/'+path.relative_to(ROOT).as_posix())
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertTrue(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()))
                z.extractall(folder)
            checkout=Path(folder)/'BLTA_reproduction'
            run=subprocess.run([sys.executable,str(checkout/'reproduce.py'),'--refit','--output',str(checkout/'fresh_results')],cwd=folder,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr[-3000:])
            report=json.loads((checkout/'fresh_results/verification.json').read_text())
            self.assertEqual(report['held_tool_folds'],90)
            self.assertTrue(report['source_heads_refitted'])
            self.assertEqual(report['archived_count_mismatches'],0)


if __name__=='__main__':
    unittest.main()
