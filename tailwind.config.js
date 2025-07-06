module.exports = {
    darkMode: 'class', // enables class-based dark mode
    content: ['./templates/**/*.html', './static/js/**/*.js'],
    theme: {
        extend: {
            colors: {
                'aws-dark-blue': '#1e3a8a',
                'aws-gray': '#374151',
            },
            fontFamily: {
                sans: ['Roboto', 'sans-serif'],
            },
        },
    },
    plugins: [],
};
