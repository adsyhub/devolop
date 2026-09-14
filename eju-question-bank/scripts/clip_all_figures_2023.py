"""Resolve explicitly marked figure bboxes into a new draft directory."""
import argparse
import copy
from pathlib import Path
from eju_bank.assets import AssetStore, clip_figure_from_pdf
from eju_bank.audit import iter_asset_nodes
from eju_bank.source import source_file, validate_source_manifest
from eju_bank.util import load_json, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--pages',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--media-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.out.resolve()==args.pages.resolve() or (args.out.exists() and any(args.out.iterdir())):
        parser.error('Choose a new, empty output directory; input page revisions are preserved')
    manifest=load_json(args.manifest);validate_source_manifest(manifest,args.manifest,verify_files=True)
    store=AssetStore(args.media_dir);assets=[]
    for path in sorted(args.pages.glob('p*.json')):
        page=copy.deepcopy(load_json(path));changed=False
        for _,node in iter_asset_nodes(page):
            if node.get('type')!='figure' or node.get('assetId'):continue
            if not node.get('sourceBbox'):parser.error(f'{path.name}: figure lacks sourceBbox')
            pdf=source_file(manifest,args.manifest,page['sourceFileRole'])
            data,_,_=clip_figure_from_pdf(pdf,page['page'],node['sourceBbox'])
            meta=store.put_bytes(data,mime_type='image/png',ext='.png')
            node['assetId']=meta['assetId'];assets.append(meta['assetId']);changed=True
        if changed:
            page.pop('reviewedBy',None);page.pop('reviewedAt',None)
            page.setdefault('issues',[]).append({'code':'review.cropped_figures','message':'New crops require comparison with the original source'})
        write_json(args.out/path.name,page)
    write_json(args.out/'asset-index.json',{'assetIds':assets,'status':'REVIEW_REQUIRED'})
    print(f'{len(assets)} crops created; new page drafts written to {args.out}')


if __name__=='__main__':main()
