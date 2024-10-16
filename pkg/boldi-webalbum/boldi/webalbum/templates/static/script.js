const THROTTLE = 100/*ms*/;

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
    // works on FF and Safari
    fullscreenScrollTarget.scrollIntoView({behavior: "instant"});
    setTimeout((target) => {
        // works on Chrome
        target.scrollIntoView({behavior: "instant"});
        scrollingResizesViewport = false;
    }, THROTTLE, fullscreenScrollTarget);
    fullscreenScrollTarget = null;
});

function defaultScrollTarget() {
    return document.querySelector("header");
}

function getCandidateScrollTargets() {
    candidates = document.querySelectorAll("header, #subfolders a[id], #thumbnails a[id], article.image, #epilogue, footer");
    lastTop = null;
    let result = []
    for (const candidate of candidates) {
        const top = candidate.getBoundingClientRect().top;
        if (top !== lastTop) {
            result.push(candidate);
        }
        lastTop = top;
    }
    return result;
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

function getCurrentScrollTarget() {
    const candidates = getCandidateScrollTargets();
    firstElement = candidates[0];
    if (isElementVisible(firstElement)) {
        return firstElement;
    }
    oneButLastElement = candidates[candidates.length - 2];
    lastElement = candidates[candidates.length - 1];
    if (!isElementVisible(oneButLastElement) && isElementVisible(lastElement)) {
        return lastElement;
    }
    for (const candidate of candidates) {
        if (isElementVisible(candidate)) {
            return candidate;
        }
    }
    return defaultScrollTarget();
}

function getUrlForElement(element) {
    const id = element.id;
    url = new URL(window.location.href);
    url.hash = id !== "top" && id && `#${id}` || "";
    return url.href;
}

function getTargetUrlForFirstVisibleScrollTarget() {
    return getUrlForElement(getCurrentScrollTarget());
}

function scrollCurrentScrollTargetIntoView(scrollBehavior) {
    scrollBehavior = scrollBehavior || "auto";
    const currentScrollTarget = getCurrentScrollTarget();
    currentScrollTarget.scrollIntoView({behavior: scrollBehavior})
}

let setUrlTimeoutId = null;
let setUrlTargetUrl = null;

function setUrl(targetUrl) {
    if (!setUrlTimeoutId && !scrollingResizesViewport) {
        window.history.replaceState({url: targetUrl}, null, targetUrl);
        setUrlTimeoutId = setTimeout(() => {
            if (setUrlTargetUrl) {
                window.history.replaceState({url: setUrlTargetUrl}, null, setUrlTargetUrl);
            }
            setUrlTargetUrl = null;
            setUrlTimeoutId = null;
        }, 2*THROTTLE);
        setUrlTargetUrl = null;
    } else {
        setUrlTargetUrl = targetUrl;
    }
}

let scrolling = false;
let scrollingTo = null;
function scrollEnd() {
    scrollHandler();
    scrolling = false;
    scrollingTo = null;    
}

let scrollHandlerThrottled = false;
let scrollHandlerTimeoutId = null;
function scrollHandler() {
    setUrl(
        scrollingTo && getUrlForElement(scrollingTo)
        || getTargetUrlForFirstVisibleScrollTarget()
    );
}

let scrollingResizesViewport = false;
function windowResizeHandler() {
    if (scrolling) {
        if (!scrollingResizesViewport) {
            url = window.location.origin + window.location.pathname + window.location.search
            window.history.replaceState({url: url}, null, url);
        }
        scrollingResizesViewport = true;
    }
}
window.addEventListener("resize", windowResizeHandler);

document.addEventListener("scroll", () => {
    scrolling = true;
    if (!scrollHandlerThrottled) {
        scrollHandlerThrottled = true;
        scrollHandlerTimeoutId = setTimeout(() => {
            scrollHandler();
            scrollHandlerThrottled = false;
        }, THROTTLE);
        scrollHandler();
    }
});

let lastWindowScrollY = window.scrollY;
let resetScrollingToTimeoutId = null;
function resetScrollingToIfStoppedScrolling() {
    // emulate "scrollend" event on iOS
    if (window.scrollY != lastWindowScrollY) {
        lastWindowScrollY = window.scrollY;
        setTimeout(resetScrollingToIfStoppedScrolling, THROTTLE)
    } else {
        scrollEnd();
    }
}

function setScrollingTo(element) {
    scrollingTo = element;
    clearTimeout(resetScrollingToTimeoutId);
    resetScrollingToTimeoutId = setTimeout(resetScrollingToIfStoppedScrolling, THROTTLE);
}

function scrollToNextScrollTarget(delta, source, _) {
    const baseTarget = scrollingTo || source || getCurrentScrollTarget();
    if (!scrollingTo && !isElementPreciselyScrolledIntoView(baseTarget) && delta === 1) {
        delta = 0;
    }
    const candidates = getCandidateScrollTargets();
    let i = 0;
    for (i = 0; i < candidates.length; i++) {
        if (candidates[i] === baseTarget) {
            const newTarget = candidates[i + delta];
            if (newTarget) {
                setUrl(getUrlForElement(newTarget));
                setScrollingTo(newTarget);
                // TODO Fix jerkiness in chrome.
                // Smooth scrolling should be disabled 
                newTarget.scrollIntoView({behavior: "instant"});
                return;
            }
        }
    }
    if (candidates[i - 1] !== baseTarget || delta !== 1) {
        // If we get stuck, try to get unstuck
        window.scrollBy({"top": 10 * delta});
    }
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
    } else if (event.key === "h") {
        document.querySelector("header").scrollIntoView();
    } else if (event.key === "e") {
        current = getCurrentScrollTarget();
        target = document.querySelector(`#${current.id}_thumbnail`) || document.querySelector("#thumbnails, #subfolders");
        target.scrollIntoView();
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

function handleLinksInSPA() {
    links = document.querySelectorAll('a[href]:not([href^="#"]):not([href^="javascript:"])');
    for (const link of links) {
        if (link.href.host !== window.location.href.host) {
            continue;
        }

        link.addEventListener("click", (event) => {
            loadLocationInSPA(link.href);
            event.preventDefault();
        });
    }
}

let spaStateUrl = window.location.href;

function loadLocationInSPA(href) {
    if (href == spaStateUrl) {
        return;
    }
    const request = new Request(href);
    window.fetch(request).then((response) => {
        if (response.ok) {
            return response.text();
        } else if (window.location.href !== href) {
            window.location.href = href;
        }
    }).then((text) => {
        const domParser = new DOMParser();
        spaStateUrl = href;
        document.querySelectorAll("img").forEach((imgElement) => {
            imgElement.src = "";
            imgElement.srcset = "";
        });
        document.baseURI = href;
        if (!(window.history.state && window.history.state.url && window.history.state.url === href)) {
            console.log("pushState", href)
            window.history.pushState({url: href}, null, href);
        }
        const page = domParser.parseFromString(text, "text/html");
        document.head.replaceWith(page.head);
        document.body.replaceWith(page.body);
        handleLinksInSPA();

        (document.querySelector(new URL(href).hash || "*") || document.documentElement).scrollIntoView();
    });
}

window.addEventListener("load", handleLinksInSPA);
window.addEventListener("load", (event) => {
    spaStateUrl = window.location.href;
    window.history.replaceState({url: spaStateUrl}, null, spaStateUrl);
});
window.addEventListener("popstate", (event) => {
    console.log("popstate", spaStateUrl, "->", event.state && event.state.url);
    if (event.state && event.state.url && event.state.url !== spaStateUrl) {
        loadLocationInSPA(event.state.url);
    }
});
