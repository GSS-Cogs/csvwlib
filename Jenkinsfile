pipeline {
    agent any
    stages {
        stage('Test') {
            agent {
                dockerfile {
                    args '-u root -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                dir("pmd") {
                    sh "pipenv sync --dev"
                    // Patch behave so that it can output the correct format for the Jenkins cucumber tool.
                    sh "patch -d \"$(pipenv --venv)/lib/python3.9/site-packages/behave/formatter\" -p1 < /cucumber-format.patch"

                    sh "pipenv run behave pmd/tests/behaviour --tags=-skip -f json.cucumber -o pmd/tests/behaviour/test-results.json"
                    dir("pmd/tests/unit") {
                        sh "PIPENV_PIPFILE='../../../Pipfile' pipenv run python -m xmlrunner -o reports *.py"
                    }

                }

                stash name: "test-results", includes: "**/test-results.json,**/reports/*.xml" // Ensure test reports are available to be reported on.
                sh "rm -rf *" // remove everything before next build (we have permissions problems since this stage is run as root)
            }
        }
    }
    post {
        always {
            script {
                try {
                    unstash name: "test-results"
                } catch (Exception e) {
                    echo "Stash does not exist"
                }
                cucumber fileIncludePattern: '**/test-results.json'
                junit allowEmptyResults: true, testResults: '**/reports/*.xml'
            }

        }
    }
}