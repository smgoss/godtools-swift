//
//  AccessibilityTapAreaView.swift
//  godtools
//
//  Created by Levi Eggert on 7/22/24.
//  Copyright © 2024 Cru. All rights reserved.
//

import SwiftUI

// NOTE: I placed this within a parent ZStack where the parent ZStack had an onTapGesture.  When using XCUITest to query the parent ZStack the tap would hit within the elements
// of the ZStack and sometimes it would hit a button within the parent ZStack.  So far placing this element with the parent ZStack and querying for this element and calling tap
// will have the same effect as tapping the parent ZStack. Example in ToolCardView.swift. ~Levi
//
// Updated 2026-05-02: filled the parent rather than a 1x1 corner anchor.
// Maestro's `tapOn id:` resolves the element's frame and taps its center;
// at 1x1 the tap landed at the card's top-left corner, which on the
// thumbnail-layout spotlight cards on Dashboard Tools fell in a region
// the simulator dropped on the floor. Color.clear has no hit testing of
// its own (no contentShape), so taps still fall through to the parent
// ZStack's .onTapGesture, and sibling controls drawn later in the ZStack
// (favorite heart, etc.) still receive their own taps normally.

struct AccessibilityTapAreaView: View {

    private let accessibilityIdentifier: String

    init(accessibilityIdentifier: String) {

        self.accessibilityIdentifier = accessibilityIdentifier
    }

    var body: some View {

        Color.clear
            .accessibilityIdentifier(accessibilityIdentifier)
    }
}
