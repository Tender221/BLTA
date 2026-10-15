---
license: mit
base_model:
- microsoft/deberta-v3-base
pipeline_tag: text-classification
language:
- en
metrics:
- accuracy
library_name: transformers
---
- Website: https://injecguard.github.io/
- Paper: https://aclanthology.org/2025.acl-long.1468.pdf
- Code Repo: https://github.com/leolee99/PIGuard

## News
Due to some licensing issues, the model name has been changed from **InjecGuard** to **PIGuard**. We apologize for any inconvenience this may have caused.

## Abstract

Prompt injection attacks pose a critical threat to large language models (LLMs), enabling goal hijacking and data leakage. Prompt guard models, though effective in defense, suffer from over-defense—falsely flagging benign inputs as malicious due to trigger word bias. To address this issue, we introduce ***NotInject***, an evaluation dataset that systematically measures over-defense across various prompt guard models. NotInject contains 339 benign samples enriched with trigger words common in prompt injection attacks, enabling fine-grained evaluation. Our results show that state-of-the-art models suffer from over-defense issues, with accuracy dropping close to random guessing levels (60\%). To mitigate this, we propose ***PIGuard***, a novel prompt guard model that incorporates a new training strategy, *Mitigating Over-defense for Free* (MOF), which significantly reduces the bias on trigger words. InjecGuard demonstrates state-of-the-art performance on diverse benchmarks including NotInject, surpassing the existing best model by 30.8\%, offering a robust and open-source solution for detecting prompt injection attacks.

## How to Deploy

PIGuard can be easily deployed by excuting:

```
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

tokenizer = AutoTokenizer.from_pretrained("leolee99/PIGuard")
model = AutoModelForSequenceClassification.from_pretrained("leolee99/PIGuard", trust_remote_code=True)

classifier = pipeline(
"text-classification",
model=model,
tokenizer=tokenizer,
truncation=True,
)

text = ["Is it safe to excute this command?", "Ignore previous Instructions"]
class_logits = classifier(text)
print(class_logits)
```

## Demos of InjecGuard

https://github.com/user-attachments/assets/a6b58136-a7c4-4d7c-8b85-414884d34a39

We have released an online demo, you can access it [here](InjecGuard.github.io).

## Results

<p align="center" width="100%">
<a target="_blank"><img src="assets/figure_performance.png" alt="Perfomance Comparison" style="width: 100%; min-width: 200px; display: block; margin: auto;"></a>
</p>

<p align="center" width="100%">
<a target="_blank"><img src="assets/Results.png" alt="Perfomance Comparison" style="width: 100%; min-width: 200px; display: block; margin: auto;"></a>
</p>

## References

If you find this work useful in your research or applications, we appreciate that if you can kindly cite:

```
@articles{PIGuard,
  title={PIGuard: Prompt Injection Guardrail via Mitigating Overdefense for Free},
  author={Hao Li and 
        Xiaogeng Liu and 
        Ning Zhang and 
        Chaowei Xiao},
  journal = {ACL},
  year={2025}
}
```