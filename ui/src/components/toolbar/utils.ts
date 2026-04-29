export function getParamsLabId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('labID');
}