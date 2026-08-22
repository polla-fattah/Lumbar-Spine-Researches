# Literature Review: Lumbar Spine MRI Grading Systems & AI Diagnostics

## Part I: Clinical Foundations & Reference Standards

Diagnostic radiology of the lumbar spine relies on standardized, morphology-based grading systems to characterize degenerative changes 1\. In clinical practice, these systems establish a common language between radiologists and spine surgeons, helping to correlate imaging findings with patient symptoms (such as low back pain or neurogenic claudication) and guide therapeutic decision-making 2, 3\.

### 1\. Intervertebral Disc Degeneration (IDD) Grading Scales

#### The Foundational Pfirrmann Classification

Developed by Christian W. A. Pfirrmann et al. in 2001, the Pfirrmann grading system remains the most widely accepted reference standard for classifying lumbar intervertebral disc degeneration (IDD) on sagittal T2-weighted MRI 1, 2\. The system evaluates the disc across four key criteria:

1. **Homogeneity and signal intensity** of the nucleus pulposus 4, 5\.  
2. **Delineation/distinction** between the nucleus pulposus and the annulus fibrosus 4, 5\.  
3. **Structural integrity** of the disc (presence of horizontal bands) 4\.  
4. **Disc height** 4, 5\.

Based on these features, IDD is categorized into five distinct ordinal grades:

* **Grade I:** The nucleus pulposus is homogeneous and bright white (hyperintense T2 signal, reflecting healthy tissue hydration) 4, 6\. The boundary between the nucleus and the annulus is sharp, and the disc height is completely normal 4\.  
* **Grade II:** The nucleus is slightly inhomogeneous, often presenting with or without horizontal gray bands, but the boundary between the nucleus and the annulus remains clear 4, 7\.  
* **Grade III:** The nucleus is inhomogeneous and has a decreased, gray signal intensity 4, 7\. The boundary between the nucleus and the annulus becomes unclear, and there may be mild loss of disc height 4\.  
* **Grade IV:** The nucleus is heterogeneous and dark gray to black (indicating advanced water loss and matrix dehydration) 4, 6\. The boundary between the nucleus and the annulus is completely indistinguishable, and there is moderate disc height loss 4\.  
* **Grade V:** The entire disc presents as a low-signal intensity (black) void on T2-weighted scans with total collapsed disc space 4, 7\.

While the Pfirrmann system is simple and universally understood, it has notable limitations, including its **subjective visual nature** (which contributes to high inter-observer variability, typically yielding Cohen's kappa values between 0.49 and 0.83) and a **lack of sensitivity to change** over time 3, 8, 9\. Additionally, it fails to account for other key biomarkers of pain and degeneration, such as **Modic changes** (marrow lesions in the adjacent vertebral endplates) or **high-intensity zones (HIZ)** (representing annular tears) 3, 4, 6\.  
\+-----------------------------------------------------------------------------------------+  
|                               PFIRRMANN GRADING AT A GLANCE                             |  
\+---------+--------------------+------------------------+------------------+--------------+  
|  Grade  | Nucleus Structure  | T2 Signal Intensity    | NP-AF Boundary   | Disc Height  |  
\+---------+--------------------+------------------------+------------------+--------------+  
|    I    | Homogeneous        | Hyperintense (Bright)  | Clear            | Normal       |  
|   II    | Inhomogeneous/Bands| Hyperintense (Bright)  | Clear            | Normal       |  
|   III   | Inhomogeneous      | Intermediate (Grey)    | Unclear          | Mild Loss    |  
|   IV    | Inhomogeneous      | Hypointense (Dark)     | Indistinct       | Moderate Loss|  
|    V    | Inhomogeneous      | Signal Void (Black)    | Lost             | Collapsed    |  
\+---------+--------------------+------------------------+------------------+--------------+

#### The Modified Pfirrmann Scale (Griffith et al., 2007\)

As the spine ages, the clinical utility of the standard Pfirrmann scale decreases due to a ceiling effect—most geriatric discs present as Grade IV or V, obscuring subtle but clinically relevant degenerative differences 10\.  
To overcome this, Griffith et al. (2007) proposed an **8-level modified Pfirrmann grading system** 10, 11\. This modified scale expands the standard grading by introducing intermediate categories, focusing heavily on fine-grained variations in **disc height** and **signal intensity loss** 10\. In a validation study of 260 lumbar discs in an elderly cohort (mean age of 73 years), the modified system proved highly discriminatory, demonstrating excellent intra-observer agreement (weighted \\\\(\\kappa\\\\) range: 0.79 to 0.91) and substantial inter-observer agreement (weighted \\\\(\\kappa\\\\) range: 0.65 to 0.67) 10\.

### 2\. Lumbar Spinal Stenosis (LSS): Central Canal Morphological Systems

To describe narrowing of the lumbar spinal canal, two major morphological grading systems have supplanted simple quantitative dural sac cross-sectional area (DSCA) measurements, which often fail to correlate with clinical claudication symptoms due to anatomical and positional variability 12, 13\.  
              SCHIZAS MORPHOLOGICAL GRADING OF CENTRAL CANAL STENOSIS  
                
     Grade A (No/Minor)            Grade B (Moderate)            Grade C (Severe)  
  \+-----------------------+     \+-----------------------+     \+-----------------------+  
  |    \\  CSF visible  /  |     |  Rootlets occupy entire|    | No rootlets visible   |  
  |     \\             /   |     |  dural sac, but can   |     | Homogeneous grey sign.||  
  | (o) (o) (o) (o) (o)   |     |  still be individualized|    |                       |  
  |   (Rootlets dorsal)   |     | (Grainy appearance)   |     | Epidural fat posterior|  
  \+-----------------------+     \+-----------------------+     \+-----------------------+  
                                                                \*Grade D (Extreme): Same  
                                                                 as C, but with total  
                                                                 loss of posterior fat.

#### The Schizas Classification (2010)

Devised by Constantin Schizas et al., this qualitative grading system is based on the **morphology of the dural sac** on axial T2-weighted MRI, specifically evaluating the **cerebrospinal fluid (CSF)-to-rootlet ratio** 12, 14\. Instead of measuring cross-sectional area, it assesses how cauda equina rootlets are arranged within the dural sac:

* **Grade A (No or Minor Stenosis):** CSF is clearly visible inside the dural sac, but its distribution is inhomogeneous 14\. It is further divided into four sub-grades:  
* **A1:** Rootlets lie dorsally and occupy less than half of the dural sac area 14\.  
* **A2:** Rootlets lie dorsally and are in contact with the dura, but are in a horseshoe configuration 14\.  
* **A3:** Rootlets lie dorsally and occupy more than half of the dural sac area 15\.  
* **A4:** Rootlets lie centrally and occupy the majority of the dural sac area 15\.  
* **Grade B (Moderate Stenosis):** Rootlets occupy the entire dural sac, but they can still be individualized 15\. Some CSF is still present, giving a characteristic **grainy appearance** to the dural sac 15\.  
* **Grade C (Severe Stenosis):** No individual rootlets can be recognized 15\. The dural sac demonstrates a homogeneous gray signal with no CSF signal visible 15\. **Posterior epidural fat is still preserved** 15\.  
* **Grade D (Extreme Stenosis):** Identical to Grade C, but **posterior epidural fat is completely obliterated** 16\.

**Clinical & Prognostic Significance:** Schizas et al. demonstrated that patients presenting with **Grades C and D** stenosis represent a highly distinct clinical group who are **statistically far more likely to fail conservative treatment** and require surgical decompression (Odds Ratio: 29.8) 17, 18\. Most Grade A and B patients with claudication did not warrant surgery for several years 18\.

#### The Lee Central Canal Stenosis grading system (2011)

G.Y. Lee et al. (2011) introduced a simplified, highly reliable qualitative grading system based on the **degree of separation of the cauda equina rootlets** on axial T2 images 19, 20:

* **Grade 0 (No Stenosis):** No lumbar stenosis, with no obliteration of the anterior CSF space 19\.  
* **Grade 1 (Mild Stenosis):** Obliteration of the anterior CSF space is present, but **all cauda equina rootlets remain separated** from one another 19\.  
* **Grade 2 (Moderate Stenosis):** Rootlets show aggregation, meaning **some of the cauda equina rootlets are aggregated** together 19\.  
* **Grade 3 (Severe Stenosis):** **None of the cauda equina rootlets are separated** (they are completely aggregated into a single mass) due to severe external compression 19\.

This system exhibits outstanding clinical reproducibility, with inter-reader intraclass correlation coefficients (ICC) ranging from 0.73 to 0.95 and intra-reader kappa values of 0.86 to 0.90 19\.

### 3\. Lumbar Spinal Stenosis: Foraminal & Lateral Recess Systems

             LEE SAGITTAL GRADING OF NEURAL FORAMINAL STENOSIS (LFS)  
               
     Grade 1 (Mild)                Grade 2 (Moderate)             Grade 3 (Severe)  
  \+-----------------------+     \+-----------------------+     \+-----------------------+  
  |   Perineural fat      |     |   Perineural fat      |     |   Nerve root          |  
  |   obliteration in     |     |   obliteration in     |     |   collapsed or        |  
  |   2 directions        |     |   all 4 directions    |     |   morphologically     |  
  |   (vertical/trans.)   |     |   (No root collapse)  |     |   changed (flattened) |  
  \+-----------------------+     \+-----------------------+     \+-----------------------+

#### The Lee Foraminal Stenosis Grading System (2010)

Neural foraminal stenosis (LFS) involves narrowing of the exit canal, compressing the nerve root as it exits the spinal cord 21, 22\. Devised by S. Lee et al. (2010), this system evaluates LFS on **parasagittal images** by focusing on **perineural fat obliteration and nerve root morphology** 23, 24:

* **Grade 0:** Normal, with no evidence of foraminal narrowing or fat obliteration 23\.  
* **Grade 1 (Mild):** Shows perineural fat obliteration in only **two opposing directions** (either vertical or transverse) 23\.  
* **Grade 2 (Moderate):** Shows perineural fat obliteration in **all four directions** surrounding the nerve root, but **without morphologic change** (no compression or flattening) of the nerve root itself 23\.  
* **Grade 3 (Severe):** Characterized by **nerve root collapse** or severe morphologic change (flattening/distortion of the root) 23\.

#### Sartoretti Foraminal Stenosis Grading

An alternative to Lee's system, Sartoretti’s classification is a **6-point sagittal grading system** (Grades A to F) 25:

* **Grade A:** No foraminal stenosis 25\.  
* **Grades B, C, D, and E:** Indicate progressive contact of the exiting nerve root with the superior, posterior, inferior, and anterior boundaries of the foramen, respectively 25\.  
* **Grade F:** Severe stenosis with distinct nerve root morphological collapse 25\.

#### Subarticular Zone (Lateral Recess) Stenosis Guidelines

The subarticular zone, extending from the medial edge of the articular facet to the edge of the neuroforamen, is a highly common site of nerve root impingement 26\. Standard clinical guidelines (including those from Lurie et al. and the consensus conference by Andreisek et al.) grade subarticular stenosis on axial T2 images using a **thickness/volume compromise ratio** 26, 27:

* **Mild:** Lateral recess space is compromised by **\\\\(\\le\\\\) 1/3** of its normal size 26\.  
* **Moderate:** Space is compromised between **1/3 and 2/3** of its normal size 26\.  
* **Severe:** Space is compromised by **\\\\(\>\\\\) 2/3** of its normal size 26\.

Nerve root impingement within this zone is clinically characterized as "none," "touching," "displacing," or "compressing" 26\.

### 4\. Lumbar Disc Herniation (LDH): MSU Size-Based Classification

While descriptive classifications (bulge, protrusion, extrusion, sequestration) characterize the shape of disc herniations 28, 29, the **Michigan State University (MSU) classification** developed by Mysliwiec et al. (2010) offers an objective, size-based metric to guide surgical selection on axial MR images 30-32:  
                      MSU CLASSIFICATION OF DISC HERNIATION SIZE  
                        
     Grade 1 (Small)               Grade 2 (Medium)               Grade 3 (Large)  
  \+-----------------------+     \+-----------------------+     \+-----------------------+  
  | Herniation            |     | Herniation            |     | Herniation extends    |  
  | extends \< 50% to      |     | extends \> 50% to      |     | completely beyond     |  
  | intra-facet line      |     | intra-facet line      |     | the intra-facet line  |  
  |          \--- \- \- \- \-  |     |          \--- \- \- \- \-  |     |          \=== \=========|  
  |          (Facet Line) |     |          (Facet Line) |     |          (Facet Line) |  
  \+-----------------------+     \+-----------------------+     \+-----------------------+  
The MSU system utilizes a single axial T2-weighted cut showing the maximal herniation and draws a **transverse intra-facet reference line** connecting the medial edges of the left and right facet joints 30:

* **Grade 0:** Normal disc (no herniation) 33\.  
* **Grade 1:** Small herniation, extending **up to (less than) 50%** of the distance from the non-herniated posterior aspect of the disc to the intra-facet line 33\.  
* **Grade 2:** Medium herniation, extending **more than 50%** of the distance to the intra-facet line, but not crossing it 33, 34\.  
* **Grade 3:** Large herniation, extending **completely beyond the intra-facet line** into the canal 33, 34\.

**Clinical & Surgical utility:** MSU size-1 lesions are strongly associated with successful conservative (non-surgical) management 35\. Conversely, size-2 or size-3 lesions frequently cause critical nerve root compression, making patients with these grades excellent candidates for microdiscectomy 32, 35\.

### Summary of Reference Standards

The table below synthesizes the anatomical targets, imaging views, and primary clinical indicators for each standard clinical grading system:  
Pathology,Grading System,Primary MRI View,Primary Morphological Indicators,Clinical Impact  
Intervertebral Disc Degeneration,"Pfirrmann (2001) 36, 37",Sagittal T2 2,"T2 signal intensity, boundary distinction, disc height 4",Baseline measure of aging/structural disease 2  
Elderly Disc Degeneration,"Modified Pfirrmann (2007) 10, 37",Sagittal T2 10,Expanded 8-level scale; precise height & signal loss 10,"Prevents ""ceiling effect"" in older cohorts 10"  
Central Canal Stenosis,Schizas (2010) 38,Axial T2 12,"CSF/rootlet morphology; dural sac shape 12, 14","Grades C & D predict conservative treatment failure 17, 18"  
Central Canal Stenosis,"Lee Central (2011) 19, 39",Axial T2 19,Obliteration of anterior CSF space; rootlet separation 19,High clinical reproducibility and ease of communication 19  
Neural Foraminal Stenosis,"Lee Foraminal (2010) 40, 41","Sagittal T1 & T2 23, 25","Perineural fat obliteration (2 vs 4 directions), root collapse 23",Correlates with exiting nerve root compression 24  
Disc Herniation Severity,"MSU Classification (2010) 32, 42",Axial T2 30,"Herniation size relative to transverse intra-facet line 30, 33",Grades 2 & 3 identify microdiscectomy candidates 35


# Literature Review: Lumbar Spine MRI Grading Systems & AI Diagnostics

## Part II: Deep Learning Paradigms & Automated Diagnostics

The transition from manual, qualitative grading systems to automated diagnostic pipelines is driven by advances in deep learning (DL). Recent neural network architectures have shifted the diagnostic paradigm from simple classification to anatomy-aware, multi-task, and multi-modal systems 1-3. These pipelines leverage advanced computer vision backbones to perform semantic segmentation, localized region of interest (ROI) extraction, and classification of complex spinal pathologies 4-6.

### 1\. Multi-Task, Multi-Pathology Diagnostic Engines

Rather than training isolated, single-purpose networks, modern clinical systems deploy multi-task architectures that share representations across different tasks to improve generalizability and data efficiency 1, 7\.  
                     SPINENET MULTI-TASK ARCHITECTURE (JAMALUDIN ET AL.)  
                       
                         \+------------------------------+  
                         |      Sagittal MR Slices      |  
                         \+--------------+---------------+  
                                        |  
                         \+--------------v---------------+  
                         |   5 Shared Conv. Layers      |  
                         \+--------+--+--+---+--+--------+  
                                  |  |  |   |  |  
            \+---------------------+  |  |   |  \+---------------------+  
            |                        |  |   |                        |  
     \+------v------+                 |  |   \+------v------+   \+------v------+  
     | Pfirrmann   |          \+------v--v-----+       | Endplate    | Marrow      |  
     | Grading     |          | Disc          |       | Defects     | Changes     |  
     \+-------------+          | Narrowing     |       \+-------------+-------------+  
                              \+---------------+

#### The SpineNet and SpineNetV2 Systems

* **SpineNet (Jamaludin et al., 2017):** SpineNet represents a major milestone in automated spine diagnostics 7, 8\. It utilizes a deep convolutional neural network (CNN) trained in a multi-task framework to predict multiple radiological scores from sagittal T2-weighted lumbar MRIs 1, 9\. The early stages of the network—the first five convolutional layers—are shared, allowing the model to learn robust joint feature representations 1\. The architecture then branches out into individual pathways to simultaneously classify six distinct radiological scores across multiple lumbar levels (from T12-L1 to L5-S1) 1\. These scores include:  
* **Pfirrmann grading** and **disc narrowing** (for intervertebral discs) 1\.  
* **Upper and lower endplate defects**, and **upper and lower marrow (Modic) changes** (for vertebral bodies) 1\.  
* A notable strength of SpineNet is its ability to train on image-level class labels without requiring dense voxel-wise segmentations or slice-level localization 1, 9\. However, a key limitation of the original SpineNet was its reliance on preprocessed sagittal disc volumes, which restricted its input data and prevented it from evaluating axial slices—thereby limiting its ability to grade central canal stenosis, disc herniation, or nerve root compression 7\.  
* **SpineNetV2 (Windsor et al., 2022):** Developed to address these limitations, SpineNetV2 expands the diagnostic footprint to grade up to **11 radiological features** simultaneously 10, 11\. Architecturally, it transitions to a multi-stage approach, employing a U-Net backbone to locate and label vertebral bodies and discs, followed by a ResNet classifier to grade individual pathologies 10\. While SpineNetV2 offers a comprehensive open-source solution, external validations have shown that its reliance on sagittal views remains a bottleneck for assessing pathologies like foraminal stenosis and disc herniation, which are best evaluated on axial scans 12, 13\.

#### Other Clinical Multi-Task Models

* **Su et al. (2022) / Axial ResNet-50 Pipeline:** Addressing the axial-view gap, Su et al. developed a multi-task ResNet-50 classification framework specifically for axial T2-weighted MRIs 14, 15\. The model uses a shared ResNet-50 feature extraction backbone coupled with three separate fully-connected layers to classify the presence and severity (Grades 0 to 3\) of **lumbar disc herniation (LDH)**, **lumbar central canal stenosis (LCCS)**, and **lumbar nerve root compression (LNRC)** 14\. The model achieved substantial diagnostic accuracies of 84.17% for LDH, 86.99% for LCCS, and 81.21% for LNRC on internal datasets 14, 16\.  
* **M-SCAN Multistage Framework (Batra et al., 2025):** Batra et al. proposed a sequence-based multi-stage architecture that integrates sagittal and axial views 2\. In the first stage, a U-Net with a ResNet50 encoder detects 2D canal stenosis coordinates on sagittal T2 images 17\. These coordinates are projected into 3D space using patient orientation data from the DICOM metadata 17\. The system then automatically selects the three closest axial slices for each of the five lumbar levels 17\. Finally, these localized axial crops are classified for stenosis severity (Normal/Mild, Moderate, Severe) using an EfficientNet classifier, achieving a predictive precision of 93.80% 2, 18\.

### 2\. Specialised Segmentation & Morphometry (U-Net & DSCA)

Automating clinical morphometry—such as calculating the **dural sac cross-sectional area (DSCA)**—requires highly precise pixel-level segmentation 19, 20\. U-Net and its specialized variants have become the standard for these dense anatomical segmentation tasks 21, 22\.  
                 SPECIALISED SEGMENTATION ARCHITECTURES COMPARED  
                   
     U-Net (Baseline)             Attention U-Net             MultiResUNet  
  \+--------------------+     \+--------------------+     \+--------------------+  
  |  Skip Connections  |     |  Attention Gates   |     |  ResPath & Multi-  |  
  |  pass spatial      |     |  suppress noise    |     |  Scale Blocks      |  
  |  features directly |     |  in background     |     |  capture fine      |  
  |  to decoder.       |     |  and focus on ROI. |     |  edges & boundaries|  
  \+--------------------+     \+--------------------+     \+--------------------+

#### The Dural Sac Cross-Sectional Area (DSCA) and MultiResUNet

Measuring the dural sac cross-sectional area (DSCA) on axial T1- or T2-weighted MRI is the gold standard for quantifying spinal canal narrowing 19, 20\. Manual tracing is slow and prone to inter-observer variability 20, 23\. To address this, George Ghobrial and Christian Roth (2025) evaluated three distinct architectures—U-Net, Attention U-Net, and **MultiResUNet**—for automated T1-weighted DSCA segmentation and quantitative area calculation 19, 24\.

* **MultiResUNet** significantly outperformed the other models 19, 25\. By replacing standard convolutions with MultiRes blocks (which capture multi-scale features) and standard skip connections with ResPaths (which mitigate semantic gaps between encoder and decoder features), MultiResUNet achieved a **Pearson correlation coefficient of 0.9917** and an exceptionally low **Mean Absolute Error (MAE) of 17.95 mm²** on the primary dataset 19, 24, 26, 27\.  
* The model demonstrated strong generalizability, maintaining an accuracy of 99.95% and an F1-score of 0.9393 on external validation 19\. It automatically calculates dural sac boundaries and outputs direct geometric measurements (in mm²) 28, 29, bridging the gap between raw pixel predictions and objective clinical indicators 29, 30\.

#### Advanced U-Net Variations for Spine Segmentation

* **Inception-Enhanced U-Net with Bottleneck Loss (Silveira et al., 2025):** Silveira et al. proposed an enhanced U-Net that integrates an Inception module at the bottleneck layer 31, 32\. The Inception block extracts features at multiple spatial scales using parallel convolutional kernels of varying sizes 31, 32\. Additionally, a dual-output mechanism provides segmentation maps at both the bottleneck and final decoder stages, improving gradient flow during training 31-33. Trained on the SPIDER dataset with Dice loss, this model achieved a mean Intersection over Union (mIoU) of 0.8974 and an F1-score of 0.9444, and was successfully extended to multiclass segmentation to separately identify vertebrae, discs, and the spinal canal 31\.  
* **DeepSPINE (Lu et al., 2018):** This framework utilizes a U-Net architecture combined with a ResNeXt-50 encoder to perform automatic whole-body lumbar vertebral segmentation, disc-level designation, and spinal stenosis grading 34, 35\.  
* **SPINEPS (Möller et al., 2025):** A semantic and instance segmentation framework designed to identify **14 distinct spinal structures** (including ten vertebra substructures, intervertebral discs, the spinal cord, and the spinal canal) in whole-body T2-weighted sagittal MRI scans, employing a sliding-window instance mask generation model 36\.

### 3\. Real-Time Detection Pipelines (YOLO Backbones)

While segmentation networks are highly precise, single-stage object detectors from the **YOLO (You Only Look Once)** family are increasingly preferred for clinical workflows due to their high inference speeds, low computational footprints, and suitability for real-time edge deployment 37-39.  
                     YOLOv5 & YOLOv8 PIPELINES FOR PATHOLOGY DETECTION  
                       
     YOLOv3 (Tsai et al.)         YOLOv5 (Wang et al.)         YOLOv8 (Yilihamu et al.)  
  \+------------------------+   \+------------------------+   \+------------------------+  
  | DarkNet-53 Backbone;   |   | Attention CSP Module;  |   | Dual-Branch Framework; |  
  | mAP of 92.4% for disc  |   | Residual SPPF;         |   | YOLOv8-seg (disc) and  |  
  | herniation detection.  |   | automated HIZ grading. |   | YOLOv8-pose (canal).   |  
  \+------------------------+   \+------------------------+   \+------------------------+

#### YOLOv3 (Tsai et al., 2021\)

Tsai et al. developed an automatic pipeline using YOLOv3 with a DarkNet-53 backbone to detect lumbar disc herniations (LDH) on sagittal T2-weighted MRIs 40, 41\. They demonstrated that single-stage detectors can achieve high performance on relatively small clinical datasets through targeted data augmentations—such as horizontal flipping, rotation, and exposure and contrast adjustments 40, 42-44. Using a 550-image dataset with data augmentation (550-aug), the model achieved a **mean average precision (mAP) of 92.4%** and a Jaccard index of 80.8% in localizing herniations 42, 44, 45\.

#### YOLOv5 & Attention Customizations (Liawrungrueang et al., 2023; Wang et al., 2025\)

* **Standard YOLOv5 (Liawrungrueang et al., 2023):** This study first validated a standard YOLOv5 detector to localize and grade lumbar disc degeneration into five Pfirrmann classes on sagittal T2 MRIs, achieving an accuracy of over 95% 46-48. The authors demonstrated its clinical utility by streaming predictions in real-time onto monitoring screens or video feeds (using a 100-epoch training protocol) to assist orthopedic surgeons during patient consultations 38, 49\.  
* **Modified YOLOv5 (Wang et al., 2025):** To improve small-object detection on sagittal and axial images, Wang et al. modified the YOLOv5 architecture 50\. They added an **attention module in the Cross Stage Partial (CSP) network** and integrated a **residual module in the Spatial Pyramid Pooling-Fast (SPPF) part** 50, 51\. This allowed the model to simultaneously detect and grade Pfirrmann degeneration, disc herniation, and high-intensity zones (HIZ) 50, 52, with over 95% of the model's outputs rated as clinically acceptable by experts 53\.

#### YOLOv8 Dual-Branch Multi-Task Model (Yilihamu et al., 2025\)

Yilihamu et al. introduced a highly sophisticated, multi-stage dual-branch workflow based on YOLOv8 for axial T2-weighted scans 6, 54:

* **Branch 1 (Segmentation):** Employs a YOLOv8 object detector to locate the intervertebral disc, followed by a **YOLOv8-seg** semantic segmentation model that classifies each pixel within the disc area 6\. This model achieved an mAP50:95 of 98.12% and a spatial Jaccard overlap (IoU) of 98.36% 54\.  
* **Branch 2 (Keypoint Detection):** Uses YOLOv8 to locate the articular processes and spinous process, feeding these regions into a **YOLOv8-pose** keypoint detection model 6\. YOLOv8-pose precisely locates the boundaries of the seven zones of the spinal canal with a mean error of just 0.208 mm 6, 54\.  
* **Classification & Severity:** Combining these branches, the model evaluates herniation severity (4 classes) and region of involvement (8 classes), achieving classification accuracies of **92.51%** and **83.34%**, respectively 54\. This demonstrates the power of the YOLOv8 framework in unifying object detection, pixel segmentation, and keypoint regression within a single, unified pipeline 6, 54\.

### Summary of Deep Learning Paradigms

The table below contrasts the technical characteristics and primary clinical targets of the major deep learning frameworks:  
Architecture Family,Key Representatives,Input Views Used,Segmentation/Detection Metrics,Clinical/Morphometric Output  
Multi-Task CNNs,"SpineNet / SpineNetV2 1, 10, Axial ResNet-50 14","Sagittal T2 1, Axial T2 14, Sagittal T1 55",SpineNetV2 external accuracy: 83.5%–97.5% 56; ResNet axial accuracy: 81.2%–87.0% 14,"Simulteneous multi-pathology grading (Pfirrmann, LCCS, Modic, LDH, spondylolisthesis) 10, 56, 57"  
U-Net & Variants,"MultiResUNet 19, Inception-UNet 31, SPINEPS 36","Axial T1 19, Sagittal T1 31, Sagittal T2 36",MultiResUNet DSC: 0.999 58; Inception-UNet mIoU: 0.897 31,"Voxel-wise masks and automated geometric measurements (e.g., DSCA in mm²) 19, 31"  
YOLO Framework,"YOLOv3 40, YOLOv5 & Modified CSP/SPPF 50, YOLOv8-seg & YOLOv8-pose 54","Sagittal T2 38, 40, 50, Axial T2 50, 54",YOLOv3 mAP: 92.4% 42; YOLOv8-seg mAP50:95: 98.12% 54,"Real-time localization, bounding box detection, keypoint extraction, and classification 6, 49, 54"

# Literature Review: Lumbar Spine MRI Grading Systems & AI Diagnostics

## Part III: Statistical Reliability, Validation & Clinical Challenges

While the technical development of deep learning (DL) models has shown remarkable progress, translating these models into clinical workflows depends heavily on three factors: bridging the **human inter-observer reliability gap**, demonstrating generalizability through **rigorous external validation**, and solving the **interpretability ("black box") challenge**.

### 1\. The Inter-Observer Reliability Gap

Standardizing subjective radiological grading systems is a major challenge in clinical spine care. Clinical grading systems suffer from substantial variability, even among highly experienced readers:

* **Human Inconsistency:** Standard Pfirrmann grading of intervertebral disc degeneration (IDD) is highly subjective. Studies show that human readers achieve only moderate inter-rater reliability, with Cohen's kappa (\\\\(\\kappa\\\\)) values varying widely between **0.491 and 0.830** 1, 2\. Intra-observer agreement is similarly limited, ranging from 0.69 to 0.81 1, 2\. This inconsistency makes it difficult to reliably track subtle degenerative changes over time or stratify patients for clinical trials.  
* **The AI Consistency Advantage:** Automated grading models can match or even exceed human consistency by providing objective, repeatable measurements. For example:  
* **Pfirrmann vs. Fujiwara Reliability:** Nikpasand et al. (2024) compared a convolutional neural network (CNN) against human graders on both Pfirrmann grading (for discs) and Fujiwara grading (for facet joint osteoarthritis) 3, 4\.  
* For Pfirrmann grading, the CNN achieved **78% percent agreement** and a **substantial Fleiss kappa of 0.68** against the lead radiologist—outperforming the average human rater's agreement (\\\\(p \< 10^{-6}\\\\)) 5, 6\.  
* For the highly complex and skewed Fujiwara facet joint grading, human agreement was poor (average human \\\\(\\kappa \= 0.13\\\\)) 7, 8\. The CNN achieved **49% agreement and a Fleiss kappa of 0.18** 5, illustrating that even in highly subjective and imbalanced clinical tasks, AI models provide a more standardized baseline than manual observation.  
* **Continuous Variable Modeling:** Niemeyer et al. (2021) addressed the clinical boundaries of Pfirrmann grading by treating grades as continuous variables rather than categorical classes 9\. They found that modeling the Pfirrmann scale continuously using linear regression reduced large, clinically significant misclassifications 9\. This continuous modeling approach correlates strongly with objective physical biomarkers, such as actual disc hydration levels 9\.

                INTER-RATER AGREEMENT COMPARISON (COHEN'S KAPPA)  
                  
     0.0 (Chance)      0.2 (Fair)        0.4 (Moderate)    0.6 (Substantial)   0.8-1.0 (Perfect)  
      |-----------------|-----------------|-----------------|-----------------|-----------------|  
        
      Facet Joint:  
      \[\#\#\#\] Human Avg (0.13)  
      \[\#\#\#\#\#\] CNN Facet Model (0.18)  
        
      Pfirrmann IDD:  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\] Human Low-End (0.49)  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\] SpineNet Ext. Val. (0.68)  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\] Human High-End (0.83)

### 2\. Rigorous External Validation & Generalizability

An AI model's performance on its training dataset often fails to translate to other institutions due to **domain shift** (differences in MRI scanner manufacturers, field strengths, slice thicknesses, and patient demographics). Independent external validation on geographically and temporally separate cohorts is the ultimate test of a model's clinical viability.

#### Validation of SpineNet on the Northern Finland Birth Cohort 1966 (NFBC1966)

The most famous and robust external validation of a spinal AI model was conducted by Terence P. McSweeney et al. (2023), who benchmarked the open-source **SpineNet** model using the **Northern Finland Birth Cohort 1966** 10, 11:

* **Study Design:** The validation utilized T2-weighted sagittal lumbar scans from **1,331 participants** (representing a total of **6,655 intervertebral discs**) 11, 12\. This dataset was completely separate—both geographically and temporally—from the UK-based GENODISC dataset used to train SpineNet 13, 14\.  
* **Performance Metrics:** SpineNet demonstrated outstanding robustness, matching the reliability of expert human raters:  
* **Disc Degeneration (Pfirrmann):** Achieved a balanced accuracy of **78%** 12, 13, with a Lin concordance correlation coefficient (Lin’s CCC) of **0.86** 12, 13 and a Cohen's \\\\(\\kappa\\\\) of **0.68** 12, 13\. Notably, while SpineNet disagreed with human raters on 20.83% of the discs, **only 0.85% of these disagreements had a grade difference greater than 1** 12, 13\.  
* **Modic Changes (MC):** Achieved a balanced accuracy of **86%** with a Cohen's \\\\(\\kappa\\\\) of **0.74** 12, 13\.  
* **Clinical Value:** This study established that a multi-task deep learning network can maintain high diagnostic reliability across geographically distinct datasets, proving that automated pipelines can reliably process large-scale epidemiological cohorts 13, 15\.

#### Comprehensive Validation of SpineNetV2

While early validations evaluated only a few pathologies, recent studies have put the updated **SpineNetV2** (which grades 11 features simultaneously) through comprehensive validation:

* **The Lumbosacral Pathology Cohort (Nigru et al., 2024):** Nigru et al. evaluated SpineNetV2 on **1,747 lumbosacral discs** from 353 symptomatic patients 16, 17\.  
* *Where it excelled:* SpineNetV2 achieved excellent agreement with expert radiologists for primary pathologies, demonstrating a Pfirrmann accuracy of **79.6%** 18 and Cohen's \\\\(\\kappa\\\\) values ranging up to **0.799** 19\.  
* *Where it struggled:* The model demonstrated lower agreement for **foraminal stenosis and disc herniation** 20, 21\. Because SpineNetV2 relies exclusively on sagittal views, it fails to capture the transverse anatomical context required to reliably grade herniations and foraminal narrowing—pathologies that clinically require axial views 20, 21\. Spondylolisthesis also showed occasional errors, where the model labeled adjacent vertebral levels as positive 22\.  
* **The Confirmatory Second Reader Study (Wu et al., 2026):** Wu et al. validated SpineNetV2 across **2,455 lumbar discs** (491 patients) against orthopedic surgeons 23\.  
* SpineNetV2 achieved an overall accuracy of **83.5% to 97.5%** across five binary pathologies, significantly outperforming a junior orthopedic surgeon in central canal stenosis, spondylolisthesis, and bilateral foraminal stenosis (\\\\(p \\le 0.001\\\\)) 23\.  
* However, Pfirrmann grading accuracy **declined significantly in older patient cohorts and upper lumbar discs** 23\. The model displayed a **specificity-oriented profile** (where false negatives exceeded false positives) 23\. Consequently, the authors concluded that SpineNetV2 is highly effective as a confirmatory "second reader" to prevent human omissions, but should not be relied upon as a primary screening tool 23\.

### 3\. The Interpretability Challenge & Explainable AI (XAI)

For clinicians to trust and adopt deep learning models, AI systems must move beyond "black box" predictions. They must provide visual and textual evidence showing *why* a decision was made.  
                          EXPLAINABLE AI DIAGNOSTIC MODALITIES  
                            
    Evidence Hotspots (Saliency)      Voxel-Wise Tissue Mapping        Vision-Language Models (VLMs)  
   \+----------------------------+   \+----------------------------+   \+----------------------------+  
   | Identifies ROIs           |   | Computes pixel-level       |   | Segments anatomy and       |  
   | (e.g., endplate, nucleus)  |   | labels (e.g., Modic Type I |   | generates radiologist-     |  
   | that drove classification. |   | vs. Type II bone marrow).  |   | style narrative reports.   |  
   \+----------------------------+   \+----------------------------+   \+----------------------------+

* **Evidence Hotspots (Saliency Maps):** In the original SpineNet framework, Jamaludin et al. (2017) introduced **evidence hotspots** 24\. By mapping the gradients of the output layer back to the input image, the network generates a visual heatmap indicating which local pixels drove the classification 24, 25\. For example, when predicting an endplate defect, the heatmap focuses on the vertebral boundaries, proving that the model utilizes anatomically correct features rather than background noise 24\.  
* **Grad-CAM & Attention Segments:** Silveira et al. (2025) integrated **Grad-CAM (Gradient-weighted Class Activation Mapping)** into their multi-scale Inception-UNet segmentation model 26, 27\. Visualizations confirmed that the network's attention was highly focused on the vertebral bodies and nucleus pulposus, showing a strong spatial correlation with manual segmentations and verifying clinical safety 27\.  
* **Voxel-Wise Modic Mapping:** Kenneth T. Gao et al. (2022) developed an interpretable, two-stage CNN framework to create **voxel-wise Modic change maps** on sagittal MRIs 28, 29\. Rather than assigning a simple class label, the model segments the bone marrow and labels individual voxels as Modic Type I, II, or normal 29\. This detailed visual mapping directly improved clinicians' diagnostic performance, significantly boosting human inter-reader agreement from a Cohen's \\\\(\\kappa\\\\) of **0.52 to 0.58** (\\\\(p \< 0.05\\\\)) 30\.  
* **Automated Radiology Report Generation (Explainable VLMs):** Representing the state-of-the-art in explainability, Islam Sk et al. (2026) introduced an **Explainable Vision-Language Model (VLM)** framework for Lumbar Spinal Stenosis 31\. The model uses a Spatial Patch Cross-Attention module for text-directed anomaly localization and an automated reporting module 31\. It translates 2D/3D segmentation masks into fluent, radiologist-style narrative reports, achieving a **diagnostic accuracy of 90.69%**, a **95.12% Dice score**, and an outstanding **92.80% CIDEr language generation score** 31\. This bridges the gap between spatial segmentation, clinical classification, and clinical communication 31\.

### Summary of Statistical Validation & XAI

Validation Cohort / Study,Model Evaluated,Primary Reliability Metrics,Key Validation Insight,Explainability Method  
Northern Finland Birth Cohort 1966 (McSweeney et al.),SpineNet (Open-source),"\\\\(\\kappa \= 0.68\\\\) (Pfirrmann), \\\\(\\kappa \= 0.74\\\\) (Modic changes)","Matched expert human reliability on a large, geographically distinct cohort",Saliency-based evidence hotspots  
"Lumbosacral Cohort (Nigru et al., 2024)",SpineNetV2 (Open-source),\\\\(\\kappa \= 0.457\\\\) to \\\\(0.799\\\\); LCCC up to \\\\(0.972\\\\),"High reliability for primary features, but dropped for foraminal stenosis & herniation",Sagittal visual overlays  
"Confirmatory Reader Cohort (Wu et al., 2026)",SpineNetv2 (Open-source),Binary accuracy: 83.5%–97.5%; lower Pfirrmann MAE (0.213),Outperformed junior surgeon; recommended as a confirmatory second reader,None (focus on statistical performance)  
"Modic Mapping Cohort (Gao et al., 2022)",Two-stage autoencoder,Bone marrow Dice: 0.88; improved human agreement from \\\\(\\kappa \= 0.52\\\\) to \\\\(0.58\\\\),Voxel-wise labeling of bone marrow lesions assists and improves human diagnostic reliability,Voxel-wise color-coded pathology maps  
"Multi-Center VLM Cohort (Islam Sk et al., 2026)",Explainable VLM,Segmentation Dice: 0.9512; Language CIDEr: 92.80%,"Solved class imbalances to generate precise, text-directed spatial localization",Automated radiology report generation

### Task Tracking Update

Let's call the manage\_tasks tool to mark Part III as complete.\# **Literature Review: Lumbar Spine MRI Grading Systems & AI Diagnostics**

## Part III: Statistical Reliability, Validation & Clinical Challenges

While the technical development of deep learning (DL) models has shown remarkable progress, translating these models into clinical workflows depends heavily on three factors: bridging the **human inter-observer reliability gap**, demonstrating generalizability through **rigorous external validation**, and solving the **interpretability ("black box") challenge**.

### 1\. The Inter-Observer Reliability Gap

Standardizing subjective radiological grading systems is a major challenge in clinical spine care. Clinical grading systems suffer from substantial variability, even among highly experienced readers:

* **Human Inconsistency:** Standard Pfirrmann grading of intervertebral disc degeneration (IDD) is highly subjective. Studies show that human readers achieve only moderate inter-rater reliability, with Cohen's kappa (\\(\\kappa\\)) values varying widely between **0.491 and 0.830** 1\. Intra-observer agreement is similarly limited, ranging from 0.69 to 0.81 1\. This inconsistency makes it difficult to reliably track subtle degenerative changes over time or stratify patients for clinical trials.  
* **The AI Consistency Advantage:** Automated grading models can match or even exceed human consistency by providing objective, repeatable measurements. For example:  
* **Pfirrmann vs. Fujiwara Reliability:** Nikpasand et al. (2024) compared a convolutional neural network (CNN) against human graders on both Pfirrmann grading (for discs) and Fujiwara grading (for facet joint osteoarthritis) 4\.  
* For Pfirrmann grading, the CNN achieved **78% percent agreement** and a **substantial Fleiss kappa of 0.68** against the lead radiologist—outperforming the average human rater's agreement (\\(p \< 10^{-6}\\)) 5, 6\.  
* For the highly complex and skewed Fujiwara facet joint grading, human agreement was poor (average human \\(\\kappa \= 0.13\\)) 8\. The CNN achieved **49% agreement and a Fleiss kappa of 0.18** 5, illustrating that even in highly subjective and imbalanced clinical tasks, AI models provide a more standardized baseline than manual observation 8\.  
* **Continuous Variable Modeling:** Niemeyer et al. (2021) addressed the clinical boundaries of Pfirrmann grading by treating grades as continuous variables rather than categorical classes 9\. They found that modeling the Pfirrmann scale continuously using linear regression reduced large, clinically significant misclassifications 9\. This continuous modeling approach correlates strongly with objective physical biomarkers, such as actual disc hydration levels 9\.

                INTER-RATER AGREEMENT COMPARISON (COHEN'S KAPPA)  
                  
     0.0 (Chance)      0.2 (Fair)        0.4 (Moderate)    0.6 (Substantial)   0.8-1.0 (Perfect)  
      |-----------------|-----------------|-----------------|-----------------|-----------------|  
        
      Facet Joint:  
      \[\#\#\#\] Human Avg (0.13)  
      \[\#\#\#\#\#\] CNN Facet Model (0.18)  
        
      Pfirrmann IDD:  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\] Human Low-End (0.49)  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\] SpineNet Ext. Val. (0.68)  
      \[\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\] Human High-End (0.83)

### 2\. Rigorous External Validation & Generalizability

An AI model's performance on its training dataset often fails to translate to other institutions due to **domain shift** (differences in MRI scanner manufacturers, field strengths, slice thicknesses, and patient demographics). Independent external validation on geographically and temporally separate cohorts is the ultimate test of a model's clinical viability.

#### Validation of SpineNet on the Northern Finland Birth Cohort 1966 (NFBC1966)

The most famous and robust external validation of a spinal AI model was conducted by Terence P. McSweeney et al. (2023), who benchmarked the open-source **SpineNet** model using the **Northern Finland Birth Cohort 1966** 11:

* **Study Design:** The validation utilized T2-weighted sagittal lumbar scans from **1,331 participants** (representing a total of **6,655 intervertebral discs**) 11, 12\. This dataset was completely separate—both geographically and temporally—from the UK-based GENODISC dataset used to train SpineNet 13, 14\.  
* **Performance Metrics:** SpineNet demonstrated outstanding robustness, matching the reliability of expert human raters:  
* **Disc Degeneration (Pfirrmann):** Achieved a balanced accuracy of **78%** 12, 13, with a Lin concordance correlation coefficient (Lin’s CCC) of **0.86** 12, 13 and a Cohen's \\(\\kappa\\) of **0.68** 12, 13\. Notably, while SpineNet disagreed with human raters on 20.83% of the discs, **only 0.85% of these disagreements had a grade difference greater than 1** 12, 13\.  
* **Modic Changes (MC):** Achieved a balanced accuracy of **86%** with a Cohen's \\(\\kappa\\) of **0.74** 13\.  
* **Clinical Value:** This study established that a multi-task deep learning network can maintain high diagnostic reliability across geographically distinct datasets, proving that automated pipelines can reliably process large-scale epidemiological cohorts 13, 15\.

#### Comprehensive Validation of SpineNetV2

While early validations evaluated only a few pathologies 32, 33, recent studies have put the updated **SpineNetV2** (which grades 11 features simultaneously) through comprehensive validation:

* **The Lumbosacral Pathology Cohort (Nigru et al., 2024):** Nigru et al. evaluated SpineNetV2 on **1,747 lumbosacral discs** from 353 symptomatic patients 16, 17\.  
* *Where it excelled:* SpineNetV2 achieved excellent agreement with expert radiologists for primary features, demonstrating a Pfirrmann accuracy of **79.6%** 18 and Cohen's \\(\\kappa\\) values ranging from **0.457 to 0.799** 19\.  
* *Where it struggled:* The model demonstrated lower agreement for **foraminal stenosis and disc herniation** 20\. Because SpineNetV2 relies exclusively on sagittal views, it fails to capture the transverse anatomical context required to reliably grade herniations and foraminal narrowing—pathologies that clinically require axial views 20, 21\. Spondylolisthesis also showed occasional errors, where the model labeled adjacent vertebral levels as positive 22\.  
* **The Confirmatory Second Reader Study (Wu et al., 2026):** Wu et al. validated SpineNetV2 across **2,455 lumbar discs** (491 patients) against orthopedic surgeons 23\.  
* SpineNetV2 achieved an overall accuracy of **83.5% to 97.5%** across five binary pathologies, significantly outperforming a junior orthopedic surgeon in central canal stenosis, spondylolisthesis, and bilateral foraminal stenosis (\\(p \\le 0.001\\)) 23\.  
* However, Pfirrmann grading accuracy **declined significantly in older patient cohorts and upper lumbar discs** 23\. The model displayed a **specificity-oriented profile** (where false negatives exceeded false positives) 23\. Consequently, the authors concluded that SpineNetV2 is highly effective as a confirmatory "second reader" to prevent human omissions, but should not be relied upon as a primary screening tool 23\.

### 3\. The Interpretability Challenge & Explainable AI (XAI)

For clinicians to trust and adopt deep learning models, AI systems must move beyond "black box" predictions. They must provide visual and textual evidence showing *why* a decision was made.  
                          EXPLAINABLE AI DIAGNOSTIC MODALITIES  
                            
    Evidence Hotspots (Saliency)      Voxel-Wise Tissue Mapping        Vision-Language Models (VLMs)  
   \+----------------------------+   \+----------------------------+   \+----------------------------+  
   | Identifies ROIs           |   | Computes pixel-level       |   | Segments anatomy and       |  
   | (e.g., endplate, nucleus)  |   | labels (e.g., Modic Type I |   | generates radiologist-     |  
   | that drove classification. |   | vs. Type II bone marrow).  |   | style narrative reports.   |  
   \+----------------------------+   \+----------------------------+   \+----------------------------+

* **Evidence Hotspots (Saliency Maps):** In the original SpineNet framework, Jamaludin et al. (2017) introduced **evidence hotspots** 24\. By mapping the gradients of the output layer back to the input image, the network generates a visual heatmap indicating which local pixels drove the classification 24, 25\. For example, when predicting an endplate defect, the heatmap focuses on the vertebral boundaries, proving that the model utilizes anatomically correct features rather than background noise 24\.  
* **Grad-CAM & Attention Segments:** Silveira et al. (2025) integrated **Grad-CAM (Gradient-weighted Class Activation Mapping)** into their multi-scale Inception-UNet segmentation model 26, 27\. Visualizations confirmed that the network's attention was highly focused on the vertebral bodies and nucleus pulposus, showing a strong spatial correlation with manual segmentations and verifying clinical safety 27\.  
* **Voxel-Wise Modic Mapping:** Kenneth T. Gao et al. (2022) developed an interpretable, two-stage CNN framework to create **voxel-wise Modic change maps** on sagittal MRIs 28, 29\. Rather than assigning a simple class label, the model segments the bone marrow and labels individual voxels as Modic Type I, II, or normal 29\. This detailed visual mapping directly improved clinicians' diagnostic performance, significantly boosting human inter-reader agreement from a Cohen's \\(\\kappa\\) of **0.52 to 0.58** (\\(p \< 0.05\\)) 30\.  
* **Automated Radiology Report Generation (Explainable VLMs):** Representing the state-of-the-art in explainability, Islam Sk et al. (2026) introduced an **Explainable Vision-Language Model (VLM)** framework for Lumbar Spinal Stenosis 31\. The model uses a Spatial Patch Cross-Attention module for text-directed anomaly localization and an automated reporting module 31\. It translates 2D/3D segmentation masks into fluent, radiologist-style narrative reports, achieving a **diagnostic accuracy of 90.69%**, a **95.12% Dice score**, and an outstanding **92.80% CIDEr language generation score** 31\. This bridges the gap between spatial segmentation, clinical classification, and clinical communication 31\.

### Summary of Statistical Validation & XAI

Validation Cohort / Study,Model Evaluated,Primary Reliability Metrics,Key Validation Insight,Explainability Method  
Northern Finland Birth Cohort 1966 (McSweeney et al.) 11,SpineNet (Open-source) 11,"\\(\\kappa \= 0.68\\) (Pfirrmann), \\(\\kappa \= 0.74\\) (Modic changes) 13","Matched expert human reliability on a large, geographically distinct cohort 13",Saliency-based evidence hotspots 24  
"Lumbosacral Cohort (Nigru et al., 2024\) 16, 17",SpineNetV2 (Open-source) 17,\\(\\kappa \= 0.457\\) to \\(0.799\\); LCCC up to \\(0.972\\) 19,"High reliability for primary features, but dropped for foraminal stenosis & herniation 20",Sagittal visual overlays 34  
"Confirmatory Reader Cohort (Wu et al., 2026\) 23",SpineNetv2 (Open-source) 23,Binary accuracy: 83.5%–97.5%; lower Pfirrmann MAE (0.213) 23,Outperformed junior surgeon; recommended as a confirmatory second reader 23,None (focus on statistical performance)  
"Modic Mapping Cohort (Gao et al., 2022\) 28, 29",Two-stage autoencoder 29,Bone marrow Dice: 0.88 35; improved human agreement from \\(\\kappa \= 0.52\\) to \\(0.58\\) 30,Voxel-wise labeling of bone marrow lesions assists and improves human diagnostic reliability 30,Voxel-wise color-coded pathology maps 29  
"Multi-Center VLM Cohort (Islam Sk et al., 2026\) 31",Explainable VLM 31,Segmentation Dice: 0.9512; Language CIDEr: 92.80% 31,"Solved class imbalances to generate precise, text-directed spatial localization 31",Automated radiology report generation 31
