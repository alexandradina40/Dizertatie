import os
import ast
import sys
import torch
import random
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm

from utils import output_cleaning
from promptloader import PromptLoader
from dataloader import CMDAD_Dataset, TVAD_Dataset, MADEval_Dataset

import base64
from google import genai
from google.genai import types

def main(args):
    # Load openai client
    client = genai.Client()
    
    # Build dataloader
    if args.dataset == "cmdad":
        D = CMDAD_Dataset 
        video_type = "movie"
    elif args.dataset == "tvad":
        D = TVAD_Dataset
        video_type = "TV series"
    elif args.dataset == "madeval":
        D = MADEval_Dataset
        video_type = "movie"
        args.num_workers = 8
    else:
        print("Check dataset name")
        sys.exit()

    # Formulate text prompt template
    general_prompt = PromptLoader(prompt_idx=args.prompt_idx, video_type=video_type, label_type=args.label_type)
    sys_prompt = ("You are an assistant trained to describe movie clips based on provided guidelines. ", 
                "Your goal is to strictly follow the given answer template for every response. ",  
                "You must avoid generic or apologetic statements like \"I'm sorry\" or \"I'm unable to.\" "
                "Combine descriptions of multiple shots into a unified response instead of describing them separately."
                )

    ad_dataset = D(model="gemini", processor=None, general_prompt=general_prompt, num_frames=args.num_frames, 
                    anno_path=args.anno_path, charbank_path=args.charbank_path, video_dir=args.video_dir, font_path=args.font_path,
                    label_type=args.label_type, label_width=args.label_width, label_alpha=args.label_alpha, 
                    prompt_idx=args.prompt_idx, adframe_label=args.adframe_label, shot_label=args.shot_label)
    
    loader = torch.utils.data.DataLoader(ad_dataset, batch_size=1, num_workers=args.num_workers, 
                                            collate_fn=ad_dataset.collate_fn, shuffle=False, pin_memory=True)

    start_sec = []
    end_sec = []
    start_sec_ = []
    end_sec_ = []
    text_gt = []
    text_gen = []
    imdbids = []
    anno_indices = []

    for idx, input_data in tqdm(enumerate(loader), total=len(loader), desc='EVAL'): 
        if args.limit is not None and idx >= args.limit:
            break
        
        video_inputs = input_data["video"][0]
        texts = input_data["prompt"][0]

        images = [types.Part.from_bytes(data=base64.b64decode(b64), mime_type="image/jpeg")
                  for b64 in video_inputs]
        config = types.GenerateContentConfig(
            system_instruction="".join(sys_prompt),
            media_resolution="MEDIA_RESOLUTION_LOW",
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
        )

        output = None
        iters = 0
        while output is None and iters < 5:
            if iters >= 1:
                print("Redo due to error")
            iters += 1
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[texts, *images],
                config=config,
            )
            output_text = response.text
            print(response.usage_metadata.prompt_token_count, "tokeni intrare")

            print(output_text)
            output_text = output_text.split("\n\n### Explanation:")[0] 
            output_text = output_text.split("\n\nExplanation:")[0] 
            output_text = output_text.split("\n### Explanation:")[0] 
            output_text = output_text.split("\nExplanation:")[0] 
            output_text = output_text.split("### Explanation:")[0] 
            output_text = output_text.split("Explanation:")[0]
            output_text = output_text.split("### Description:\n\n")[-1] 
            output_text = output_text.split("Description:\n\n")[-1] 
            output_text = output_text.split("### Description:\n")[-1] 
            output_text = output_text.split("Description:\n")[-1]
            output_text = output_text.split("### Description:")[-1]
            output_text = output_text.split("Description:")[-1]
            output = output_cleaning(output_text)
        print(output)
            
        anno_indices.extend(input_data["anno_idx"])
        imdbids.extend(input_data["imdbid"])
        text_gt.extend(input_data["gt_text"])
        text_gen.extend([output]) 
        start_sec.extend(input_data["start"])
        end_sec.extend(input_data["end"])
        start_sec_.extend(input_data["start_"])
        end_sec_.extend(input_data["end_"])
       
    # Saving
    output_df = pd.DataFrame.from_records({'anno_idx': anno_indices, 'imdbid': imdbids, 'start': start_sec, 'end': end_sec, 'start_': start_sec_, 'end_': end_sec_, 'text_gt': text_gt, 'text_gen': text_gen})
    save_path = os.path.join(args.save_dir, f"{args.dataset}_ads", "stage1_gemeni.csv")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    output_df.to_csv(save_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Base
    parser.add_argument('--batch_size', default=1, type=int)
    parser.add_argument('--dataset', default=None, type=str)
    parser.add_argument('--prompt_idx', default=0, type=int)
    parser.add_argument('--num_frames', default=16, type=int, help='number of frames')
    parser.add_argument('-j', '--num_workers', default=8, type=int, help='init mode')
    parser.add_argument('--seed', default=42, type=int, help='evaluation seed')
    parser.add_argument('--limit', default=None, type=int, help='ruleaza doar primele N descrieri')
    # Inputs
    parser.add_argument('--anno_path', default=None, type=str)
    parser.add_argument('--charbank_path', default=None, type=str)
    parser.add_argument('--video_dir', default=None, type=str)
    parser.add_argument('--save_dir', default=None, type=str)
    parser.add_argument('--font_path', default=None, type=str)
    # Label setup
    parser.add_argument('--label_type', default="circles", type=str)
    parser.add_argument('--label_width', default=10, type=int, help='label_width, 10 in a canvas 1000')
    parser.add_argument('--label_alpha', default=0.8, type=float)
    parser.add_argument('--shot_label', action='store_true', help='shot number on the top left')
    parser.add_argument('--adframe_label', action='store_true', help='AD interval frames outlined by red boxes')

    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed(args.seed)
    
    main(args)

    
    