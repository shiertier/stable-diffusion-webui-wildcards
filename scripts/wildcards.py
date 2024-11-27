import os
import random
import sys

from modules import scripts, script_callbacks, shared

class WildcardsScript(scripts.Script):
    def __init__(self):
        self.default_positive_prefix = "__artists__, very aesthetic, highres, high definition, sensitive, masterpiece, best quality, amazing quality, very aesthetic, absurdres, "
        self.default_negative_prefix = "NSFW, text, watermark, bad anatomy, bad proportions, extra limbs, extra digit, extra legs, extra legs and arms, disfigured, missing arms, too many fingers, fused fingers, missing fingers, unclear eyes, watermark, username, "

    def title(self):
        return "Wildcards"

    def show(self, is_img2img): 
        return scripts.AlwaysVisible
    
    def replace_wildcard(self, text, gen):
        if " " in text or len(text) == 0:
            return text

        wildcards_dir = shared.cmd_opts.wildcards_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "wildcards"
        )

        replacement_file = os.path.join(wildcards_dir, f"{text}.txt")
        if os.path.exists(replacement_file):
            with open(replacement_file, encoding="utf8") as f:
                replacement = gen.choice(f.read().splitlines())
                print(f"__{text}__ -> {replacement}")
                return replacement
        
        return text

    def replace_prompts(self, prompts, seeds, is_negative=False):
        results = []
        for i, text in enumerate(prompts):

            prefix = self.default_negative_prefix if is_negative else self.default_positive_prefix
            text = prefix + text
            
            gen = random.Random()
            seed = seeds[0 if shared.opts.wildcards_same_seed else i]
            gen.seed(seed)
            
            # 替换所有 __wildcard__ 标记
            parts = text.split("__")
            replaced = "".join(self.replace_wildcard(chunk, gen) for chunk in parts)
            results.append(replaced)
            
        return results

    def apply_wildcards(self, p, attr, infotext_suffix):
        if all_original_prompts := getattr(p, attr, None):
            is_negative = 'negative' in attr
            # 替换wildcards
            setattr(p, attr, self.replace_prompts(all_original_prompts, p.all_seeds, is_negative))
            # 从infotext中移除所有wildcard相关内容
            if shared.opts.wildcards_write_infotext:
                original_text = all_original_prompts[0]
                parts = original_text.split("__")
                cleaned_text = "".join(parts[::2])  # 只保留非wildcard部分
                if cleaned_text != all_original_prompts[0]:
                    p.extra_generation_params[f"Wildcard {infotext_suffix}"] = cleaned_text

    def process(self, p, *args):
        # 处理不同类型的提示词
        self.apply_wildcards(p, 'all_prompts', 'prompt')
        self.apply_wildcards(p, 'all_negative_prompts', 'negative prompt')

def on_ui_settings():
    shared.opts.add_option(
        "wildcards_same_seed",
        shared.OptionInfo(
            False,
            "对所有图片使用相同的随机种子",
            section=("wildcards", "Wildcards")
        )
    )
    
    shared.opts.add_option(
        "wildcards_write_infotext", 
        shared.OptionInfo(
            False, 
            "将原始提示词写入到infotext", 
            section=("wildcards", "Wildcards")
        ).info("在应用__wildcards__之前的原始提示词")
    )

script_callbacks.on_ui_settings(on_ui_settings) 
