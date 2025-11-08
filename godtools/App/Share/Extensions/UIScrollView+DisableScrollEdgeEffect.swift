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
        // Use KVC to avoid compile-time dependency on newer SDK symbols.
        if #available(iOS 26.0, *) {
            let edgeKeys = ["topEdgeEffect", "bottomEdgeEffect", "leftEdgeEffect", "rightEdgeEffect"]
            edgeKeys.forEach { key in
                if let effectView = (self as NSObject).value(forKey: key) as? UIView {
                    effectView.isHidden = true
                }
            }
        }
    }
}
