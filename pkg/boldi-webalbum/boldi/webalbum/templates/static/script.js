let fullscreenScrollTarget = null;

function toggleFullScreen() {
    fullscreenScrollTarget = getCurrentScrollTarget();
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen({navigationUI: "hide"});
    } else {
        document.exitFullscreen();
    }
}

document.addEventListener("fullscreenchange", (event) => {
    fullscreenScrollTarget = fullscreenScrollTarget || getCurrentScrollTarget();
    fullscreenScrollTarget.scrollIntoView({behavior: "instant"});
    fullscreenScrollTarget = null;
});

function defaultScrollTarget() {
    return document.querySelector("header");
}

function getCandidateScrollTargets() {
    return document.querySelectorAll("header, #subfolders, #thumbnails, article.image, footer");
}

function getCurrentScrollTarget() {
    return /*window.location.hash && document.querySelector(window.location.hash) |*/ getFirstVisibleScrollTarget();
}

function isElementVisible(element) {
    const viewport = window.visualViewport;
    const rect = element.getBoundingClientRect();
    return (rect.top <= viewport.offsetTop + viewport.height &&
        viewport.offsetTop < rect.bottom - rect.height * 0.1875
    );
}

function isElementPreciselyScrolledIntoView(element) {
    const viewport = window.visualViewport;
    const rect = element.getBoundingClientRect();
    return (viewport.offsetTop -5 <= rect.top && rect.top <= viewport.offsetTop + 5);
}

function getFirstVisibleScrollTarget() {
    const candidates = getCandidateScrollTargets();
    firstElement = candidates[0];
    if (isElementVisible(firstElement)) {
        return firstElement;
    }
    lastElement = candidates[candidates.length - 1];
    if (isElementVisible(lastElement)) {
        return lastElement;
    }
    for (const candidate of candidates) {
        if (isElementVisible(candidate)) {
            return candidate;
        }
    }
    return defaultScrollTarget();
}

function getTargetUrlFirFirstVisibleScrollTarget() {
    const id = getFirstVisibleScrollTarget().id;
    return id && `#${id}` || window.location.origin + window.location.pathname + window.location.search;
}

function scrollCurrentScrollTargetIntoView(scrollBehavior) {
    scrollBehavior = scrollBehavior || "auto";
    const currentScrollTarget = getCurrentScrollTarget();
    currentScrollTarget.scrollIntoView({behavior: scrollBehavior})
}

function setUrlHash(hash) {
    const targetUrl = `#${hash}` || window.location.origin + window.location.pathname + window.location.search;
    // window.history.replaceState(null, null, targetUrl);
    if (getCurrentScrollTarget() === scrollingTo) {
        scrollingTo = null;
    }
}

document.addEventListener("scrollend", (event) => {
    scrollingTo = null;
});

scrollingTo = null;
function scrollToNextScrollTarget(next, source, setHash) {
    const baseTarget = scrollingTo || source || getCurrentScrollTarget();
    if (!scrollingTo && !isElementPreciselyScrolledIntoView(baseTarget) && next === 1) {
        next = 0;
    }
    const candidates = getCandidateScrollTargets();
    for (let i = 0; i < candidates.length; i++) {
        if (candidates[i] === baseTarget) {
            const newTarget = candidates[i + next];
            if (newTarget) {
                if (setHash && newTarget.id) {
                    setUrlHash(newTarget.id)
                }
                scrollingTo = newTarget;
                newTarget.scrollIntoView();
                return;
            }
        }
    }
    // If we get stuck, try to get unstuck
    window.scrollBy({"top": 10 * next});
    scrollingTo = null;
}

document.addEventListener("keydown", (event) => {
    if (
        // Ignore if following modifier is active.
        event.getModifierState("Fn") ||
        event.getModifierState("Hyper") ||
        event.getModifierState("OS") ||
        event.getModifierState("Super") ||
        event.getModifierState("Meta") ||
        event.getModifierState("Win")
    ) {
        return;
    } else if (
        event.key === "ArrowDown"
        || event.key === "PageDown"
        || event.key === "ArrowRight" 
        || event.key === "j"
        || (event.key === " " && !event.shiftKey)) {
        scrollToNextScrollTarget(+1, null, true);
    } else if (
        event.key === "ArrowUp"
        || event.key === "PageUp"
        || event.key === "ArrowLeft"
        || event.key === "k"
        || (event.key === " " && event.shiftKey)) {
        scrollToNextScrollTarget(-1, null, true);
    } else if (event.key === ".") {
        scrollToNextScrollTarget(0, null, true);
    } else if (event.key === "h" || event.key === "e") {
        document.querySelector("header").scrollIntoView();
    } else if (event.key === "l") {
        document.querySelector("footer").scrollIntoView();
    } else if (event.key === "g") {
        document.querySelector("#thumbnails, #subfolders").scrollIntoView();
    } else if (event.key === "p") {
        document.querySelector("#images").scrollIntoView();
    } else if (event.key === "f" || event.key === "Enter") {
        toggleFullScreen();
    } else if (event.key == "q" || event.key === "Escape") {
        if (document.fullscreenElement) {
            fullscreenScrollTarget = getCurrentScrollTarget();
            document.exitFullscreen();
        }
    } else {
        // DON'T let event.preventDefault() run if event isn't handled 
        return;
    }
    event.preventDefault();
});
