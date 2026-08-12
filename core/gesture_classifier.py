import math
from config.constants import WIDTH, HEIGHT

class GestureClassifier:
    """
    Robust, angle-tolerant, and perspective-aware 21-landmark hand gesture classifier.
    Supports: OK (👌), PINCH (🤏), FIST (✊), PEACE (✌️), PALM (🖐️), and NONE.
    """
    
    @staticmethod
    def classify(landmarks):
        if not landmarks or len(landmarks) < 21:
            return "NONE", 999.0, False

        wrist = landmarks[0]
        thumb_tip = landmarks[4]

        index_mcp = landmarks[5]
        index_pip = landmarks[6]
        index_tip = landmarks[8]

        middle_mcp = landmarks[9]
        middle_pip = landmarks[10]
        middle_tip = landmarks[12]

        ring_mcp = landmarks[13]
        ring_pip = landmarks[14]
        ring_tip = landmarks[16]

        pinky_mcp = landmarks[17]
        pinky_pip = landmarks[18]
        pinky_tip = landmarks[20]

        def dist(p1, p2):
            return math.hypot((p1.x - p2.x) * WIDTH, (p1.y - p2.y) * HEIGHT)

        palm_size = max(dist(wrist, middle_mcp), 45.0)

        def is_extended(tip, pip, mcp):
            return (dist(tip, wrist) > dist(pip, wrist) * 1.10) and (dist(tip, mcp) > palm_size * 0.72)

        def is_curled(tip, pip, mcp):
            return (dist(tip, wrist) < dist(pip, wrist) * 1.05) or (dist(tip, mcp) < palm_size * 0.62)

        idx_ext = is_extended(index_tip, index_pip, index_mcp)
        idx_crl = is_curled(index_tip, index_pip, index_mcp)

        mid_ext = is_extended(middle_tip, middle_pip, middle_mcp)
        mid_crl = is_curled(middle_tip, middle_pip, middle_mcp)

        rng_ext = is_extended(ring_tip, ring_pip, ring_mcp)
        rng_crl = is_curled(ring_tip, ring_pip, ring_mcp)

        pnk_ext = is_extended(pinky_tip, pinky_pip, pinky_mcp)
        pnk_crl = is_curled(pinky_tip, pinky_pip, pinky_mcp)

        # Distance between thumb tip and index tip / first joint
        index_dip = landmarks[7]
        thumb_idx_dist = min(dist(thumb_tip, index_tip), dist(thumb_tip, index_dip))
        is_pinched = (thumb_idx_dist < (0.38 * palm_size)) or (thumb_idx_dist < 48.0)

        # -----------------------------------------------------
        # 1. Thai Classical Dance "Jeeb" / PINCH (จีบนิ้ว 🤏)
        # Thumb & Index pinched together + other 3 fingers raised/fanned gracefully
        # -----------------------------------------------------
        open_fingers_count = int(mid_ext or not mid_crl) + int(rng_ext or not rng_crl) + int(pnk_ext or not pnk_crl)
        if is_pinched:
            # If fingers are fanned outwards/raised (Thai Jeeb) or curled (standard pinch)
            return "PINCH", thumb_idx_dist, True

        # -----------------------------------------------------
        # 2. OK Gesture (👌)
        # -----------------------------------------------------
        thumb_index_touch = (thumb_idx_dist < (0.45 * palm_size)) or (thumb_idx_dist < 56.0)
        if thumb_index_touch and (not mid_crl) and (open_fingers_count >= 2):
            return "OK", thumb_idx_dist, True

        # -----------------------------------------------------
        # 3. FIST (✊ / Grab)
        # High-accuracy: at least 3 of 4 fingers curled, no finger extended, compact span
        # -----------------------------------------------------
        curled_count = int(idx_crl) + int(mid_crl) + int(rng_crl) + int(pnk_crl)
        no_finger_extended = not (idx_ext or mid_ext or rng_ext or pnk_ext)
        max_tip_to_wrist = max(dist(index_tip, wrist), dist(middle_tip, wrist), dist(ring_tip, wrist), dist(pinky_tip, wrist))
        is_compact_fist = max_tip_to_wrist < (palm_size * 1.35)

        if (curled_count >= 3) and no_finger_extended and is_compact_fist:
            return "FIST", thumb_idx_dist, is_pinched

        # -----------------------------------------------------
        # 4. PEACE (✌️)
        # Index & Middle extended, Ring & Pinky curled
        # -----------------------------------------------------
        if idx_ext and mid_ext and rng_crl and pnk_crl:
            if dist(index_tip, middle_tip) > palm_size * 0.16:
                return "PEACE", thumb_idx_dist, is_pinched

        # -----------------------------------------------------
        # 5. OPEN PALM (🖐️)
        # High-tolerance: all 4 fingers uncurled, at least 3 extended, thumb spread
        # -----------------------------------------------------
        all_uncurled = (not idx_crl) and (not mid_crl) and (not rng_crl) and (not pnk_crl)
        extended_count = int(idx_ext) + int(mid_ext) + int(rng_ext) + int(pnk_ext)
        thumb_spread = dist(thumb_tip, index_mcp) > (palm_size * 0.45)

        if all_uncurled and (extended_count >= 3) and thumb_spread:
            return "PALM", thumb_idx_dist, is_pinched

        return "NONE", thumb_idx_dist, is_pinched
