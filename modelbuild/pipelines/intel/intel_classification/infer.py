import torch
import json
import torchvision.transforms as T
import torch.nn.functional as F
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"


def model_fn(model_dir):
    model = torch.jit.load(f"{model_dir}/model.scripted.pt")

    model.to(device).eval()
    
    return model

# data preprocessing
def input_fn(request_body, request_content_type):
    assert request_content_type == "application/json"
    
    # transform as per model selected from Timm : default ones are for resnet18
    transforms = T.Compose([
        T.ToTensor(),
        T.Resize((224, 224)),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    data = json.loads(request_body)["inputs"]
    data = np.array(data, dtype = np.uint8) # otherwise T.ToTensor() not work
    data = transforms(data)
    data = data.unsqueeze(0)
    return data


# inference
def predict_fn(input_object, model):
    with torch.no_grad():
        prediction = model(input_object)
    return prediction


# postprocess
def output_fn(predictions, content_type):
    assert content_type == "application/json"
    
    classnames = ['buildings', 'forest', 'glacier', 'mountain', 'sea', 'street']
    
    res = predictions.cpu().numpy().tolist()
    res_t = torch.tensor(res)
    conf = F.softmax(res_t, dim=-1) 
    confidences = {classnames[i]: float(conf[0][i]) for i in range(conf.shape[1])}
    confidences = sorted(confidences.items(), key=lambda x: x[1], reverse=True) 
    top5 = dict(confidences[0: 5]) 
    return json.dumps(top5)