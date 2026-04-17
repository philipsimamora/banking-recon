pipeline {
    agent any

    environment {
        SONAR_PROJECT_KEY = 'banking-recon'
        APP_DIR = '/opt/banking-recon'
        PYTHON = 'python3'
        JAVA_HOME = '/usr/lib/jvm/temurin-21-jre-amd64'
    }

    stages {

        stage('Checkout') {
            steps {
                echo '=== Cloning Repository ==='
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                echo '=== Setting up Virtual Environment ==='
                sh '''
                    ${PYTHON} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo '=== Running Unit Tests ==='
                sh '''
                    . venv/bin/activate
                    pytest --cov=. --cov-report=xml --cov-report=term \
                           -v --tb=short || true
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo '=== Running SonarQube Scan ==='
                withSonarQubeEnv('SonarQube-Local') {
                    sh "${tool('SonarQube_Scanner')}/bin/sonar-scanner"
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo '=== Checking Quality Gate ==='
                timeout(time: 3, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('Deploy to VPS') {
            when {
                branch 'main'
            }
            steps {
                echo '=== Deploying Microservices ==='
                sh '''
                    # Buat direktori jika belum ada
                    mkdir -p ${APP_DIR}

                    # Copy project files
                    rsync -av --exclude='venv' --exclude='__pycache__' \
                          --exclude='*.pyc' --exclude='.git' \
                          . ${APP_DIR}/

                    # Setup venv di app directory
                    cd ${APP_DIR}
                    ${PYTHON} -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt --quiet

                    # Restart services via supervisor
                    sudo supervisorctl restart banking-transaction || true
                    sudo supervisorctl restart banking-statement || true
                    sudo supervisorctl restart banking-reconciliation || true
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline SUCCESS'
        }
        failure {
            echo '❌ Pipeline FAILED'
        }
        always {
            cleanWs()
        }
    }
}