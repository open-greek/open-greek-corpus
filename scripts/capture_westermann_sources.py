#!/usr/bin/env python3
"""Capture direct scan renderings or verify committed Westermann scope evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import westermann_source_observations as observations

ROOT=Path(__file__).resolve().parents[1]
RENDERER_VERSION='1.28.2'
RENDER_DPI=110
JPEG_QUALITY=90
# Main historical text, complete modern indices, title and corrigenda, plus the
# source preface where Westermann explains the edition and manuscript sources.
PAGES=(5,*range(7,29),*range(29,517))


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=1)+'\n').encode()
def recipe_pins():
 return {n:sha((Path(__file__).resolve().parent/n).read_bytes()) for n in
  ('westermann_source_observations.py','capture_westermann_sources.py')}


def check(root=ROOT):
 root=Path(root)
 raw=encoded(observations.source_review(root))
 if (root/observations.REVIEW_PATH).read_bytes()!=raw:
  raise ValueError('Westermann source observations no longer reproduce')
 capture=json.loads((root/observations.CAPTURE_PATH).read_bytes())
 if capture.get('source')!=observations.SOURCE or capture.get('recipe_sha256')!=recipe_pins():
  raise ValueError('Westermann source or capture recipe changed')
 if capture.get('review_sha256')!=sha(raw):raise ValueError('Westermann source review hash changed')
 files=capture.get('files',[])
 if [x['source_pdf_page'] for x in files]!=list(PAGES):raise ValueError('Westermann source image accounting changed')
 for item in files:
  expected=f'{observations.OUTPUT}/source-evidence/page-{item["source_pdf_page"]:04d}.jpg'
  if item['path']!=expected or sha((root/item['path']).read_bytes())!=item['sha256']:
   raise ValueError('Westermann source image changed: '+expected)
 return capture


def capture(root,pdf):
 root=Path(root);pdf=Path(pdf)
 if sha(pdf.read_bytes())!=observations.SOURCE['sha256']:raise ValueError('Westermann source PDF pin changed')
 import pymupdf
 if pymupdf.VersionBind!=RENDERER_VERSION:raise ValueError('Westermann capture renderer version changed')
 document=pymupdf.open(pdf)
 if len(document)!=observations.SOURCE['pdf_pages']:raise ValueError('Westermann PDF page accounting changed')
 out=root/observations.OUTPUT;out.mkdir(parents=True,exist_ok=True)
 raw=encoded(observations.source_review(root));files=[]
 with tempfile.TemporaryDirectory(prefix='westermann-capture-') as tmp:
  staged=Path(tmp)
  for page in PAGES:
   image=document[page-1].get_pixmap(dpi=RENDER_DPI,alpha=False).tobytes('jpeg',jpg_quality=JPEG_QUALITY)
   name=f'page-{page:04d}.jpg';(staged/name).write_bytes(image)
   files.append({'path':f'{observations.OUTPUT}/source-evidence/{name}',
    'sha256':sha(image),'source_pdf_page':page,'source_pdf_sha256':observations.SOURCE['sha256']})
  target=out/'source-evidence';target.mkdir(exist_ok=True)
  for item in files:
   name=Path(item['path']).name;(target/name).write_bytes((staged/name).read_bytes())
  (root/observations.REVIEW_PATH).write_bytes(raw)
  manifest={'schema_version':1,'reviewed_at':observations.REVIEWED_AT,
   'source':observations.SOURCE,'recipe_sha256':recipe_pins(),'review_sha256':sha(raw),
   'render':{'provider':'PyMuPDF','version':RENDERER_VERSION,'dpi':RENDER_DPI,'format':'JPEG','jpeg_quality':JPEG_QUALITY,'images_retouched':False},
   'files':files,'qualification':'Direct full-page source renderings retained for complete page accounting and source-role review. The PDF pin, contents, and explicit boundary observations supply attribution; Greek spelling is not corrected by this capture.'}
  (root/observations.CAPTURE_PATH).write_bytes(encoded(manifest))
  # Remove only obsolete renders of these exact owned page numbers after every
  # replacement and metadata file has been written successfully.
  for page in PAGES:
   (target/f'page-{page:04d}.png').unlink(missing_ok=True)
 document.close()
 return check(root)


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,default=ROOT)
 parser.add_argument('--pdf',type=Path)
 parser.add_argument('--check',action='store_true')
 args=parser.parse_args()
 if args.check:result=check(args.root)
 else:
  if args.pdf is None:parser.error('--pdf is required for capture')
  result=capture(args.root,args.pdf)
 print(json.dumps({'source_pdf_pages':len(result['files']),'review_sha256':result['review_sha256']},sort_keys=True))

if __name__=='__main__':main()
