//
//  UIScrollView+DisableScrollEdgeEffect.swift
//  godtools
//
//  Created by Levi Eggert on 9/30/25.
//  Copyright © 2025 Cru. All rights reserved.
//

import UIKit

extension UIScrollView {
    
    func disableScrollEdgeEffect() {
        // Hide new iOS 18+ scroll edge effects without depending on SDK symbols
        // by using KVC to find and hide the effect views when available.
        if #available(iOS 26, *) {
            let edgeKeys = ["topEdgeEffect", "bottomEdgeEffect", "leftEdgeEffect", "rightEdgeEffect"]
            edgeKeys.forEach { key in
                if let effectView = (self as NSObject).value(forKey: key) as? UIView {
                    effectView.isHidden = true
                }
            }
        }
    }
}
