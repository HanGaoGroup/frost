"""Copy the selected proposal figure crops into assets/img as web-sized JPEGs.

Usage: python3 tools/images.py [path/to/proposal/figures/crops]
Writes assets/img/<name>.jpg (max 1600 px wide) and assets/img/t/<name>.jpg (max 720 px).
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_SRC = os.path.join(
    os.path.dirname(ROOT),
    "NSF-26-512-Unlocking-Dataset-Value-for-AI-Enabled-Scientific-Discovery-AI-Datasets-",
    "figures", "crops")

# web name -> source crop (all from the team's own archives and publications)
IMAGES = {
    # facility and tunnel experiments (Hu)
    "irt-facility": "t1_irt", "irt-iced-wing": "h2_e2", "irt-layout": "v3_s_tun",
    "irt-glaze-horns": "sc4", "ice-rime-texture": "h2_e3",
    "hs-airfoil": "f3t_hs", "hs-leading-edge": "v3_hs",
    "dip-film": "f3t_dip2", "dip-fringe": "f3t_fringe", "dip-droplet": "f3t_drop",
    "dip-film-sequence": "p14_film", "dip-rivulet": "sc3",
    "mtt-droplet": "sc2", "dih-droplets": "sc1", "ice-crystals": "f3t_xtal",
    "scan-airfoil": "f3t_scan", "scan-s1223": "v3_q1_big", "scan-propeller": "f3t_pscan",
    "scan-growth": "f9_c600", "scan-roughness": "h2_c3", "scan-rotor-sections": "t1_rig",
    "piv-propeller": "f3t_piv", "piv-s1223": "v3_s_piv", "cp-s1223": "ml_cp",
    "loads-unsteady": "f3t_loads",
    "ir-plasma": "f3t_ir3", "plasma-glow": "h2_p4", "plasma-blade": "f2_q4_big",
    "coating-compare": "f2_q4_s1", "coating-runback": "h2_p3", "heater-ir": "f2_q4_s2",
    "rotor-ice-sequence": "f10_d_top", "rotor-heating": "f10_c_top",
    "propeller-glaze": "sc5b", "engine-fan": "f5_eng", "cable-iced": "f5_infra",
    "wing-icing-photo": "f5_air",
    # field campaigns (Hu)
    "uav-iced": "sc6", "uav-instrumented": "f10_a_top", "uav-inflight-ice": "f10_b_bot",
    "uav-power": "f2_q3_big", "uav-trajectory": "v3_traj", "uav-fixedwing": "h2_e5",
    "uav-quadcopter": "t1_field2", "uav-onboard-rivulets": "f2_q3_s1",
    # high-fidelity simulation (Jain)
    "wmles-leading-edge": "f3t_sim", "wmles-rime": "v3_c1", "wmles-stall": "v3_c3",
    "crm65-surface-flow": "v3_c2", "crm65-scans": "t1_les2", "naca-ice-shapes": "f7_a",
    "wmles-cp-glaze": "f3_cpj", "cht-les": "v3_cfd_b", "cht-vs-ir": "f7_d",
    "cht-cases": "f11_s2", "artificial-vs-real-ice": "f7_c", "wmles-roughness": "h2_c6",
    "wmles-airfoil": "v3_cfd_a",
    # ISU simulations and AI (Gao, He)
    "s1223-les-fields": "f7_f", "s1223-les-mean": "f3_e", "s1223-rans": "f3_d",
    "s1223-les-3d": "v3_s_les", "irt402": "f9_a402", "irt403": "f9_a403", "irt405": "f9_a405",
    "ice-model-fields": "h2_a1", "ice-shape-band": "f7_g",
    "physminer-vortices": "f8_b", "physminer-triple": "f8_c", "physminer-arch": "h1_a5",
    "physminer-session": "h2_a4", "physminer-iddes": "h1_c2",
    "convlstm-exp": "f9_b_exp", "convlstm-pred": "f9_b_pred",
    # AI-native views
    "view-tensor": "ml_piv", "view-vector": "ml_cp", "view-graph": "ml_scan",
    "view-sdf": "ml_sdf", "view-tokens": "ml_log", "view-record": "ml_rec",
    # communities and outreach
    "community-uas": "f5_uas2", "community-cfd": "f5_cfd2", "community-ai": "f5_ai",
    "outreach-reu": "v3_bi_reu", "outreach-lab": "bi_a", "outreach-tour": "bi_c",
    "uas-military": "bi_mil",
}


def save(im, path, max_w, quality):
    im = im.copy()
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = os.path.join(ROOT, "assets", "img")
    os.makedirs(os.path.join(out, "t"), exist_ok=True)
    for name, crop in IMAGES.items():
        im = Image.open(os.path.join(src, crop + ".jpg")).convert("RGB")
        save(im, os.path.join(out, name + ".jpg"), 1600, 84)
        save(im, os.path.join(out, "t", name + ".jpg"), 720, 80)
    print(f"{len(IMAGES)} images written to {out}")


if __name__ == "__main__":
    main()
