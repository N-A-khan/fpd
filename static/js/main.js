document.addEventListener(
    "DOMContentLoaded",
    function () {

        const imageInput =
            document.getElementById(
                "productImage"
            );

        const preview =
            document.getElementById(
                "imagePreview"
            );

        if (imageInput && preview) {

            imageInput.addEventListener(
                "change",
                function () {

                    const file =
                        this.files[0];

                    if (!file) {
                        preview.innerHTML = "";
                        return;
                    }

                    const reader =
                        new FileReader();

                    reader.onload =
                        function (event) {

                            preview.innerHTML =
                                `
                                <img
                                    src="${event.target.result}"
                                    class="img-fluid rounded"
                                    style="max-height:300px;"
                                >
                                `;

                        };

                    reader.readAsDataURL(file);

                }
            );

        }

    }
);