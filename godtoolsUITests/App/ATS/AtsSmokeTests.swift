//
//  AtsSmokeTests.swift
//  godtoolsUITests
//
//  Created by Codex on 2025-11-08.
//

import XCTest

class AtsSmokeTests: BaseFlowTests {
    
    // Helper: wait for a WKWebView to load
    private func assertWebViewLoads(timeout: TimeInterval = 10) {
        let webViewExists = app.webViews.firstMatch.waitForExistence(timeout: timeout)
        XCTAssertTrue(webViewExists, "Expected a web view to load content.")
    }
}

// MARK: - godtoolsapp.com (menu web pages)

extension AtsSmokeTests {
    
    func test_GodToolsApp_TermsOfUse_WebViewLoads() {
        // Launch to Dashboard > Tools
        launchApp(flowDeepLinkUrl: "godtools://org.cru.godtools/dashboard/tools", checkInitialScreenExists: .dashboardTools)
        
        // Open Menu, then Terms of Use (https://godtoolsapp.com/terms-of-use/)
        assertIfButtonDoesNotExistElseTap(buttonAccessibility: .dashboardMenu)
        assertIfButtonDoesNotExistElseTap(buttonAccessibility: .termsOfUse)
        
        // Assert the WKWebView exists and is visible
        assertWebViewLoads()
    }
}

// MARK: - cru.org (AEM articles)

extension AtsSmokeTests {
    
    func test_CruOrg_AemArticle_WebViewLoads() {
        // A known AEM article URL (https://cru.org/...)
        let aemUri = "https://cru.org/content/experience-fragments/shared-library/language-masters/es/questions_about_god_/-quien-es-el-espiritu-santo-/godtools-variation/.html"
        let encodedUri = aemUri.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? aemUri
        let deeplink = "https://godtoolsapp.com/article/aem?uri=\(encodedUri)"
        
        // Launch without initial screen assertion (article view doesn't expose a screen id)
        launchAppWithoutInitialScreen(flowDeepLinkUrl: deeplink)
        
        // Assert the WKWebView exists and is visible
        assertWebViewLoads()
    }
}

// MARK: - YouTube (embedded video player)

extension AtsSmokeTests {
    
    func test_YouTube_OnboardingVideo_PresentsPlayer() {
        // Launch straight to Onboarding tutorial via UI-tests deep link
        launchApp(flowDeepLinkUrl: "godtools://org.cru.godtools/ui_tests/onboarding?appLanguageCode=en", checkInitialScreenExists: .onboardingTutorial)
        
        // Tap the Watch Video button and assert the video screen appears
        assertIfButtonDoesNotExistElseTap(buttonAccessibility: .watchOnboardingTutorialVideo)
        assertIfScreenDoesNotExist(screenAccessibility: .watchOnboardingTutorialVideo)
    }
}

