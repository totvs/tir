pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                bat '%repos%\\testgrounds\\appserverkiller.cmd > nul 2> nul' || true
                bat 'scripts\\install_package.cmd' || true
                bat '%repos%\\testgrounds\\appserverstarter.cmd' || true
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
				bat 'python %repos%\\MATA030TESTSUITE.py'
				bat 'python %repos%\\MATA410TESTSUITE.py'
            }
        }
    }
}
