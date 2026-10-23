let video = null;
let stream = null;


async function startCamera() {

    video =
        document.getElementById(
            "camera"
        );

    if (!video) {
        return;
    }

    try {

        stream =
            await navigator.mediaDevices
                .getUserMedia({
                    video: {
                        facingMode: "environment"
                    }
                });

        video.srcObject = stream;

        video.play();

    } catch (error) {

        console.error(
            "Camera error:",
            error
        );

        alert(
            "Unable to access camera."
        );

    }

}


function stopCamera() {

    if (stream) {

        stream
            .getTracks()
            .forEach(
                track => track.stop()
            );

    }

}